# -*- coding: utf-8 -*-
"""学习笔记本业务服务。"""

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.knowledge import KnowledgeRetrievalAgent
from app.agent.quiz_review import QuizReviewAgent
from app.agent.vision import VisionClient
from app.agent.workflow import NotebookAgentWorkflow
from app.core import settings
from app.db.model import Notebook, NotebookSource, StudioArtifact, User
from app.db.repositories import NotebookRepositories, ProfileRepositories
from app.schemas import ProfileData
from app.schemas.notebook import NotebookNoteCreate, QuizAttemptSubmit, StudioArtifactGenerate
from app.utils import Error
from app.utils.attachment import validate_image_attachment, validate_pdf_source
from .context import make_agent_messages, make_source_summary
from .serializers import (
    dump_artifact,
    dump_attachment,
    dump_message,
    dump_note,
    dump_notebook,
    dump_profile,
    dump_source,
)
from .storage import (
    cleanup_source_vectors,
    delete_source_file,
    delete_stored_file,
    get_source_file,
    get_stored_file,
)


class NotebookService:
    """NotebookLM风格学习工作区服务层。"""

    def __init__(
            self,
            session: AsyncSession,
            current_user: User,
            workflow: NotebookAgentWorkflow | None = None,
            vision_client: VisionClient | None = None,
            quiz_review_agent: QuizReviewAgent | None = None,
    ):
        """
        初始化学习笔记本服务
        :param session: 数据库会话
        :param current_user: 当前登录用户
        :param workflow: 笔记本智能体工作流
        :param vision_client: 视觉模型客户端
        :param quiz_review_agent: 测验复盘画像智能体
        :return:
        """
        self.session = session
        self.current_user = current_user
        self.workflow = workflow
        self.vision_client = vision_client
        self.quiz_review_agent = quiz_review_agent
        self.repo = NotebookRepositories(session=session)
        self.profile_repo = ProfileRepositories(session=session)

    async def create_notebook(self, title: str, description: str = "") -> dict[str, Any]:
        """
        创建学习笔记本
        :param title: 笔记本标题
        :param description: 学习说明
        :return:
        """
        row = await self.repo.create_notebook(
            user_id=self.current_user.id,
            title=title.strip(),
            description=description.strip(),
        )
        await self.session.commit()
        return {
            "errcode": 0,
            "notebook": dump_notebook(row),
        }

    async def list_notebooks(self) -> dict[str, Any]:
        """
        查询当前用户的学习笔记本
        :return:
        """
        rows = await self.repo.list_notebooks(user_id=self.current_user.id)
        return {
            "errcode": 0,
            "notebooks": [dump_notebook(row) for row in rows],
        }

    async def delete_notebook(self, notebook_id: int) -> dict[str, int]:
        """
        删除学习笔记本及其附件和知识库来源文件
        :param notebook_id: 笔记本id
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        try:
            stored_paths = await self.repo.list_attachment_paths(notebook_id=notebook.id)
            source_paths = await self.repo.list_source_paths(notebook_id=notebook.id)
            await self.session.commit()

            knowledge_agent = KnowledgeRetrievalAgent()
            await knowledge_agent.delete_notebook_collection(
                user_id=self.current_user.id,
                notebook_id=notebook.id,
            )

            notebook = await self._get_notebook(notebook_id=notebook_id)
            await self.repo.delete_notebook(notebook=notebook)
            await self.session.commit()
            for stored_path in stored_paths:
                await delete_stored_file(stored_path=stored_path)
            for stored_path in source_paths:
                await delete_source_file(stored_path=stored_path)
            return {"errcode": 0}
        except Exception as e:
            await self.session.rollback()
            raise Error(code=500, message=f"删除笔记本失败：{e}") from e

    async def get_workspace(self, notebook_id: int) -> dict[str, Any]:
        """
        获取学习笔记本工作区数据
        :param notebook_id: 笔记本id
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        messages = await self.repo.list_messages(notebook_id=notebook.id)
        message_attachments = await self.repo.list_message_attachments(
            message_ids=[row.id for row in messages],
        )
        unsent_attachments = await self.repo.list_unsent_attachments(
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        sources = await self.repo.list_sources(
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        artifacts = await self.repo.list_artifacts(
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        notes = await self.repo.list_notes(
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        profile = await self.profile_repo.get_profile(
            user_id=self.current_user.id,
            notebook_id=notebook.id,
        )
        return {
            "errcode": 0,
            "notebook": dump_notebook(notebook),
            "sources": [dump_source(row) for row in sources],
            "source_feature_status": "ready",
            "pending_attachments": [
                dump_attachment(row)
                for row in unsent_attachments
            ],
            "messages": [
                dump_message(row, message_attachments.get(row.id))
                for row in messages
            ],
            "artifacts": [dump_artifact(row) for row in artifacts],
            "notes": [dump_note(row) for row in notes],
            "profile": dump_profile(profile),
        }

    async def upload_attachment(
            self,
            notebook_id: int,
            filename: str,
            content_type: str,
            content: bytes,
    ) -> dict[str, Any]:
        """
        上传并解析中央对话图片附件
        :param notebook_id: 笔记本id
        :param filename: 原始文件名
        :param content_type: 图片MIME类型
        :param content: 图片二进制
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        original_name = Path(filename).name[:256]
        if not original_name:
            raise Error(code=400, message="附件文件名不能为空")
        if not content:
            raise Error(code=400, message="附件内容不能为空")
        if len(content) > settings.chat_attachment_max_bytes:
            raise Error(code=400, message="单个附件不能超过10MB")
        unsent_attachments = await self.repo.list_unsent_attachments(
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        if len(unsent_attachments) >= 4:
            raise Error(code=400, message="每个笔记本最多保留4张待发送图片")
        validate_image_attachment(
            filename=original_name,
            content_type=content_type,
            content=content,
        )
        await self.session.commit()

        vision_client = self.vision_client or VisionClient()
        extracted_content = await vision_client.describe_image(
            content=content,
            content_type=content_type,
        )
        unsent_attachments = await self.repo.list_unsent_attachments(
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        if len(unsent_attachments) >= 4:
            raise Error(code=400, message="每个笔记本最多保留4张待发送图片")

        stored_path = str(Path(str(notebook.id)) / f"{uuid4().hex}{Path(original_name).suffix.lower()}")
        target = get_stored_file(stored_path=stored_path)
        await asyncio.to_thread(target.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(target.write_bytes, content)
        try:
            row = await self.repo.create_attachment(
                notebook_id=notebook.id,
                user_id=self.current_user.id,
                attachment_type="image",
                original_name=original_name,
                stored_path=stored_path,
                content_type=content_type,
                file_size=len(content),
                extracted_content=extracted_content,
            )
            await self.session.commit()
            return {
                "errcode": 0,
                "attachment": dump_attachment(row),
            }
        except Exception as e:
            await self.session.rollback()
            await delete_stored_file(stored_path=stored_path)
            raise Error(code=500, message=f"保存附件失败：{e}") from e

    async def delete_attachment(self, notebook_id: int, attachment_id: int) -> dict[str, int]:
        """
        删除尚未发送的中央对话图片附件
        :param notebook_id: 笔记本id
        :param attachment_id: 图片附件id
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        row = await self.repo.get_pending_attachment(
            attachment_id=attachment_id,
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        if row is None:
            raise Error(code=404, message="待发送附件不存在")
        stored_path = row.stored_path
        await self.repo.delete_attachment(attachment=row)
        await self.session.commit()
        await delete_stored_file(stored_path=stored_path)
        return {"errcode": 0}

    async def upload_source(
            self,
            notebook_id: int,
            filename: str,
            content_type: str,
            content: bytes,
    ) -> dict[str, Any]:
        """
        上传PDF并入库到当前笔记本专属知识库
        :param notebook_id: 笔记本id
        :param filename: 原始文件名
        :param content_type: 文件MIME类型
        :param content: PDF二进制
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        original_name = Path(filename).name[:256]
        if not original_name:
            raise Error(code=400, message="PDF文件名不能为空")
        if not content:
            raise Error(code=400, message="PDF内容不能为空")
        if len(content) > settings.knowledge_pdf_max_bytes:
            raise Error(code=400, message="单个PDF不能超过10MB")
        source_count = await self.repo.count_sources(
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        if source_count >= settings.knowledge_pdf_max_files:
            raise Error(code=400, message="每个笔记本最多上传5份PDF来源")
        validate_pdf_source(
            filename=original_name,
            content_type=content_type,
            content=content,
        )

        stored_path = str(Path(str(notebook.id)) / f"{uuid4().hex}.pdf")
        target = get_source_file(stored_path=stored_path)
        await asyncio.to_thread(target.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(target.write_bytes, content)
        collection_name = KnowledgeRetrievalAgent.notebook_collection_name(
            user_id=self.current_user.id,
            notebook_id=notebook.id,
        )
        source: NotebookSource | None = None
        try:
            source = await self.repo.create_source(
                notebook_id=notebook.id,
                user_id=self.current_user.id,
                original_name=original_name,
                stored_path=stored_path,
                content_type=content_type,
                file_size=len(content),
                qdrant_collection=collection_name,
            )
            await self.session.commit()

            knowledge_agent = KnowledgeRetrievalAgent()
            ingest_result = await knowledge_agent.ingest_pdf(
                user_id=self.current_user.id,
                notebook_id=notebook.id,
                source_id=source.id,
                file_path=target,
                original_name=original_name,
            )
            source.page_count = int(ingest_result["page_count"])
            source.chunk_count = int(ingest_result["chunk_count"])
            source.text_page_count = int(ingest_result["text_page_count"])
            source.ocr_page_count = int(ingest_result["ocr_page_count"])
            source.extraction_method = str(ingest_result["extraction_method"])
            source.status = "ready"
            await self.session.commit()
            return {
                "errcode": 0,
                "source": dump_source(source),
            }
        except Error:
            await self.session.rollback()
            if source is not None:
                await cleanup_source_vectors(collection_name, source.id)
                await self._delete_source_row_after_failed_ingest(
                    source_id=source.id,
                    notebook_id=notebook.id,
                )
            await delete_source_file(stored_path=stored_path)
            raise
        except Exception as e:
            await self.session.rollback()
            if source is not None:
                await cleanup_source_vectors(collection_name, source.id)
                await self._delete_source_row_after_failed_ingest(
                    source_id=source.id,
                    notebook_id=notebook.id,
                )
            await delete_source_file(stored_path=stored_path)
            raise Error(code=500, message=f"PDF入库失败：{e}") from e

    async def delete_source(self, notebook_id: int, source_id: int) -> dict[str, int]:
        """
        删除单个PDF来源及其向量切片
        :param notebook_id: 笔记本id
        :param source_id: 来源id
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        source = await self.repo.get_source(
            source_id=source_id,
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        if source is None:
            raise Error(code=404, message="PDF来源不存在")
        stored_path = source.stored_path
        collection_name = source.qdrant_collection
        await self.session.commit()
        try:
            knowledge_agent = KnowledgeRetrievalAgent()
            await knowledge_agent.delete_source(
                collection_name=collection_name,
                source_id=source_id,
            )
            source = await self.repo.get_source(
                source_id=source_id,
                notebook_id=notebook.id,
                user_id=self.current_user.id,
            )
            if source is not None:
                await self.repo.delete_source(source=source)
            await self.session.commit()
            await delete_source_file(stored_path=stored_path)
            return {"errcode": 0}
        except Error:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise Error(code=500, message=f"删除PDF来源失败：{e}") from e

    async def stream_chat(
            self,
            notebook_id: int,
            message: str,
            attachment_ids: list[int] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        流式执行中央对话并保存结果
        :param notebook_id: 笔记本id
        :param message: 用户问题
        :param attachment_ids: 待发送图片附件id
        :return:
        """
        try:
            notebook = await self._get_notebook(notebook_id=notebook_id)
            attachment_ids = attachment_ids or []
            if not message.strip() and not attachment_ids:
                raise Error(code=400, message="请输入问题或上传附件")
            attachments = await self.repo.list_pending_attachments(
                attachment_ids=attachment_ids,
                notebook_id=notebook.id,
                user_id=self.current_user.id,
            )
            if len(attachments) != len(attachment_ids):
                raise Error(code=400, message="附件不存在、已发送或不属于当前笔记本")
            user_message = await self.repo.create_message(
                notebook_id=notebook.id,
                role="user",
                content=message.strip() or "请分析我上传的附件。",
            )
            await self.repo.bind_attachments_to_message(
                attachments=attachments,
                message_id=user_message.id,
            )
            await self.session.commit()
            yield {
                "event": "user_message",
                "message": dump_message(user_message, attachments),
            }
            messages = await self.repo.list_messages(notebook_id=notebook.id)
            message_attachments = await self.repo.list_message_attachments(
                message_ids=[row.id for row in messages],
            )
            sources = await self.repo.list_sources(
                notebook_id=notebook.id,
                user_id=self.current_user.id,
            )
            current_profile = await self.profile_repo.get_profile(
                user_id=self.current_user.id,
                notebook_id=notebook.id,
            )
            agent_messages = make_agent_messages(
                messages=messages,
                message_attachments=message_attachments,
            )
            current_profile_data = current_profile.profile_data if current_profile else None
            await self.session.commit()
            workflow = self.workflow or NotebookAgentWorkflow()
            stream = workflow.stream_chat(
                notebook_title=notebook.title,
                messages=agent_messages,
                current_profile=current_profile_data,
                user_id=notebook.user_id,
                notebook_id=notebook.id,
                source_summary=make_source_summary(sources),
            )
            workflow_state: dict[str, Any] | None = None
            async for workflow_event in stream:
                if workflow_event["event"] != "complete":
                    yield workflow_event
                    continue
                workflow_state = workflow_event["state"]
            if workflow_state is None:
                raise Error(code=500, message="智能体工作流没有返回完成事件")
            profile_result = workflow_state["profile_result"]
            profile = await self.profile_repo.save_profile(
                user_id=self.current_user.id,
                notebook_id=notebook.id,
                profile_data=profile_result.profile.model_dump(mode="json"),
                reason=profile_result.reason,
            )
            generated_artifacts = []
            for generated in workflow_state.get("generated_artifacts", []):
                artifact = await self._save_reviewed_studio_artifact(
                    notebook_id=notebook.id,
                    request=generated["request"],
                    workflow_state=generated["workflow_state"],
                )
                generated_artifacts.append((
                    artifact,
                    generated["workflow_state"]["trace"],
                ))
            assistant_message = await self.repo.create_message(
                notebook_id=notebook.id,
                role="assistant",
                content=workflow_state["answer"],
            )
            await self.session.commit()
            for artifact, agent_trace in generated_artifacts:
                yield {
                    "event": "artifact",
                    "artifact": dump_artifact(artifact),
                    "agent_trace": agent_trace,
                }
            yield {
                "event": "complete",
                "message": dump_message(assistant_message),
                "profile": dump_profile(profile),
                "agent_trace": workflow_state["trace"],
            }
        except Error as e:
            await self.session.rollback()
            yield {
                "event": "error",
                "message": e.message,
            }
        except Exception as e:
            await self.session.rollback()
            yield {
                "event": "error",
                "message": f"笔记本对话失败：{e}",
            }

    async def generate_artifact(
            self,
            notebook_id: int,
            request: StudioArtifactGenerate,
    ) -> dict[str, Any]:
        """
        生成并保存Studio学习产物
        :param notebook_id: 笔记本id
        :param request: Studio生成请求
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        try:
            messages = await self.repo.list_messages(notebook_id=notebook.id)
            message_attachments = await self.repo.list_message_attachments(
                message_ids=[row.id for row in messages],
            )
            profile = await self.profile_repo.get_profile(
                user_id=self.current_user.id,
                notebook_id=notebook.id,
            )
            agent_messages = make_agent_messages(
                messages=messages,
                message_attachments=message_attachments,
            )
            profile_data = profile.profile_data if profile else {}
            await self.session.commit()
            workflow = self.workflow or NotebookAgentWorkflow()
            workflow_state = await workflow.run_studio(
                notebook_title=notebook.title,
                messages=agent_messages,
                profile=ProfileData.model_validate(profile_data),
                request=request,
            )
            artifact = await self._save_reviewed_studio_artifact(
                notebook_id=notebook.id,
                request=request,
                workflow_state=workflow_state,
            )
            await self.session.commit()
            return {
                "errcode": 0,
                "artifact": dump_artifact(artifact),
                "agent_trace": workflow_state["trace"],
            }
        except Error:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise Error(code=500, message=f"Studio生成失败：{e}") from e

    async def delete_artifact(self, notebook_id: int, artifact_id: int) -> dict[str, int]:
        """
        删除Studio学习产物
        :param notebook_id: 笔记本id
        :param artifact_id: 产物id
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        artifact = await self.repo.get_artifact(
            artifact_id=artifact_id,
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        if artifact is None:
            raise Error(code=404, message="Studio产物不存在")
        await self.repo.delete_artifact(artifact=artifact)
        await self.session.commit()
        return {"errcode": 0}

    async def submit_quiz_attempt(
            self,
            notebook_id: int,
            artifact_id: int,
            request: QuizAttemptSubmit,
    ) -> dict[str, Any]:
        """
        提交完整测验作答，生成点评并更新学习画像
        :param notebook_id: 笔记本id
        :param artifact_id: 测验产物id
        :param request: 测验作答提交请求
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        artifact = await self.repo.get_artifact(
            artifact_id=artifact_id,
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        if artifact is None or artifact.artifact_type != "quiz":
            raise Error(code=404, message="测验内容不存在")
        attempt_summary = self._build_quiz_attempt_summary(
            artifact_data=artifact.artifact_data,
            answers=request.answers,
        )
        current_profile = await self.profile_repo.get_profile(
            user_id=self.current_user.id,
            notebook_id=notebook.id,
        )
        current_profile_data = current_profile.profile_data if current_profile else {}
        await self.session.commit()

        agent = self.quiz_review_agent or QuizReviewAgent()
        try:
            result = await agent.run(
                notebook_title=notebook.title,
                quiz_title=artifact.title,
                current_profile=current_profile_data,
                attempt_summary=attempt_summary,
            )
            profile = await self.profile_repo.save_profile(
                user_id=self.current_user.id,
                notebook_id=notebook.id,
                profile_data=result.profile.model_dump(mode="json"),
                reason=result.reason,
            )
            artifact.artifact_data = {
                **(artifact.artifact_data or {}),
                "latest_quiz_review": {
                    "correct_count": attempt_summary["correct_count"],
                    "total_count": attempt_summary["total_count"],
                    "score_percent": attempt_summary["score_percent"],
                    "review": result.review,
                    "profile_reason": result.reason,
                },
            }
            await self.session.commit()
            return {
                "errcode": 0,
                "correct_count": attempt_summary["correct_count"],
                "total_count": attempt_summary["total_count"],
                "score_percent": attempt_summary["score_percent"],
                "review": result.review,
                "profile": dump_profile(profile),
                "artifact": dump_artifact(artifact),
            }
        except Error:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise Error(code=500, message=f"测验点评失败：{e}") from e

    async def create_note(self, notebook_id: int, request: NotebookNoteCreate) -> dict[str, Any]:
        """
        创建笔记本手动笔记
        :param notebook_id: 笔记本id
        :param request: 创建笔记请求
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        note = await self.repo.create_note(
            user_id=self.current_user.id,
            notebook_id=notebook.id,
            title=request.title.strip(),
            content=request.content.strip(),
        )
        await self.session.commit()
        return {
            "errcode": 0,
            "note": dump_note(note),
        }

    async def save_message_as_note(self, notebook_id: int, message_id: int) -> dict[str, Any]:
        """
        将辅导回复保存为笔记
        :param notebook_id: 笔记本id
        :param message_id: 消息id
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        message = await self.repo.get_message(
            message_id=message_id,
            notebook_id=notebook.id,
        )
        if message is None or message.role != "assistant":
            raise Error(code=404, message="可保存的对话回复不存在")
        note = await self.repo.create_note(
            user_id=self.current_user.id,
            notebook_id=notebook.id,
            title=f"对话笔记 #{message.id}",
            content=message.content,
            note_type="chat",
        )
        await self.session.commit()
        return {
            "errcode": 0,
            "note": dump_note(note),
        }

    async def delete_note(self, notebook_id: int, note_id: int) -> dict[str, int]:
        """
        删除笔记本笔记
        :param notebook_id: 笔记本id
        :param note_id: 笔记id
        :return:
        """
        notebook = await self._get_notebook(notebook_id=notebook_id)
        note = await self.repo.get_note(
            note_id=note_id,
            notebook_id=notebook.id,
            user_id=self.current_user.id,
        )
        if note is None:
            raise Error(code=404, message="笔记不存在")
        await self.repo.delete_note(note=note)
        await self.session.commit()
        return {"errcode": 0}

    async def _get_notebook(self, notebook_id: int) -> Notebook:
        """
        获取当前用户拥有的学习笔记本
        :param notebook_id: 笔记本id
        :return:
        """
        row = await self.repo.get_notebook(
            notebook_id=notebook_id,
            user_id=self.current_user.id,
        )
        if row is None:
            raise Error(code=404, message="笔记本不存在")
        return row

    @staticmethod
    def _build_quiz_attempt_summary(
            artifact_data: dict[str, Any],
            answers: list[int],
    ) -> dict[str, Any]:
        """
        校验测验答案并生成复盘摘要
        :param artifact_data: 测验产物结构化数据
        :param answers: 每题选择的选项下标
        :return:
        """
        items = artifact_data.get("items") if isinstance(artifact_data, dict) else None
        if not isinstance(items, list) or not items:
            raise Error(code=400, message="测验内容结构不完整")
        if len(answers) != len(items):
            raise Error(code=400, message="需要完成全部题目后再提交")

        reviewed_items = []
        correct_count = 0
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise Error(code=400, message="测验题目结构不完整")
            options = item.get("options")
            answer_index = item.get("answer")
            selected_index = answers[index]
            if not isinstance(options, list) or not options:
                raise Error(code=400, message="测验选项结构不完整")
            if not isinstance(answer_index, int) or answer_index < 0 or answer_index >= len(options):
                raise Error(code=400, message="测验正确答案结构不完整")
            if selected_index >= len(options):
                raise Error(code=400, message="提交的答案超出选项范围")

            is_correct = selected_index == answer_index
            correct_count += int(is_correct)
            reviewed_items.append({
                "index": index + 1,
                "question": str(item.get("question", "")).strip(),
                "selected_option": str(options[selected_index]),
                "correct_option": str(options[answer_index]),
                "is_correct": is_correct,
                "explanation": str(item.get("explanation", "")).strip(),
            })

        total_count = len(items)
        return {
            "total_count": total_count,
            "correct_count": correct_count,
            "score_percent": round(correct_count / total_count * 100, 2),
            "items": reviewed_items,
        }

    async def _save_reviewed_studio_artifact(
            self,
            notebook_id: int,
            request: StudioArtifactGenerate,
            workflow_state: dict[str, Any],
    ) -> StudioArtifact:
        """
        保存已完成生成和质检的Studio产物
        :param notebook_id: 笔记本id
        :param request: Studio生成请求
        :param workflow_state: Studio工作流状态
        :return:
        """
        artifact = workflow_state["artifact"]
        artifact_data = {
            **artifact["artifact_data"],
            "agent_trace": workflow_state["trace"],
            "quality_approved": workflow_state["approved"],
        }
        return await self.repo.create_artifact(
            user_id=self.current_user.id,
            notebook_id=notebook_id,
            artifact_type=request.artifact_type,
            title=artifact["title"],
            content=artifact["content"],
            artifact_data=artifact_data,
            custom_prompt=request.custom_prompt,
        )

    async def _delete_source_row_after_failed_ingest(
            self,
            source_id: int,
            notebook_id: int,
    ) -> None:
        """
        PDF入库失败后尽力删除已创建的来源记录
        :param source_id: 来源id
        :param notebook_id: 笔记本id
        :return:
        """
        try:
            source = await self.repo.get_source(
                source_id=source_id,
                notebook_id=notebook_id,
                user_id=self.current_user.id,
            )
            if source is not None:
                await self.repo.delete_source(source=source)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
