# -*- coding: utf-8 -*-
"""笔记本中央对话 SSE 与 Studio 产物接口路由。"""

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from .common import raise_notebook_http_error
from app.db.model import User
from app.db.session import SessionLocal, get_session
from app.schemas.notebook import NotebookChat, QuizAttemptSubmit, StudioArtifactGenerate
from app.service.notebook import NotebookService
from app.utils import Error

router = APIRouter()


@router.post("/{notebook_id}/chat")
async def chat_with_notebook(
        notebook_id: int,
        resp: NotebookChat,
        current_user: User = Depends(get_current_user),
):
    """
    通过SSE流式返回中央对话结果
    :param notebook_id: 笔记本id
    :param resp: 对话请求
    :param current_user: 当前登录用户
    :return:
    """
    async def event_stream():
        """
        生成中央对话SSE事件
        :return:
        """
        yield ": connected\n\n"
        async with SessionLocal() as session:
            service = NotebookService(session=session, current_user=current_user)
            async for event in service.stream_chat(
                    notebook_id=notebook_id,
                    message=resp.message,
                    attachment_ids=resp.attachment_ids,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(
        content=event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "Content-Encoding": "identity",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{notebook_id}/artifacts")
async def generate_studio_artifact(
        notebook_id: int,
        resp: StudioArtifactGenerate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    生成Studio学习产物
    :param notebook_id: 笔记本id
    :param resp: Studio生成请求
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.generate_artifact(
            notebook_id=notebook_id,
            request=resp,
        )
    except Error as e:
        raise_notebook_http_error(e)


@router.delete("/{notebook_id}/artifacts/{artifact_id}")
async def delete_studio_artifact(
        notebook_id: int,
        artifact_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    删除Studio学习产物
    :param notebook_id: 笔记本id
    :param artifact_id: 产物id
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.delete_artifact(
            notebook_id=notebook_id,
            artifact_id=artifact_id,
        )
    except Error as e:
        raise_notebook_http_error(e)


@router.post("/{notebook_id}/artifacts/{artifact_id}/quiz-attempt")
async def submit_quiz_attempt(
        notebook_id: int,
        artifact_id: int,
        resp: QuizAttemptSubmit,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    提交完整测验作答，生成点评并更新画像
    :param notebook_id: 笔记本id
    :param artifact_id: 测验产物id
    :param resp: 测验作答结果
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.submit_quiz_attempt(
            notebook_id=notebook_id,
            artifact_id=artifact_id,
            request=resp,
        )
    except Error as e:
        raise_notebook_http_error(e)
