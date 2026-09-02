import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.model import Notebook, StudioArtifact, User
from app.schemas import ProfileAgentResult, ProfileData
from app.schemas.notebook import NotebookNoteCreate, StudioArtifactGenerate
from app.service.notebook import NotebookService


class WaitingChatWorkflow:
    """保持运行直到测试主动释放的可控对话工作流。"""

    def __init__(self):
        """
        初始化可控的对话工作流
        :return:
        """
        self.release = None

    async def stream_chat(
            self,
            notebook_title,
            messages,
            current_profile,
            user_id,
            notebook_id,
            source_summary,
    ):
        """
        模拟长时间运行的中央对话工作流
        :param notebook_title: 笔记本标题
        :param messages: 对话消息
        :param current_profile: 当前画像
        :param user_id: 当前用户 ID
        :param notebook_id: 当前笔记本 ID
        :param source_summary: 当前资料来源摘要
        :return:
        """
        import asyncio

        self.release = asyncio.Event()
        yield {
            "event": "status",
            "message": "generating",
        }
        await self.release.wait()
        yield {
            "event": "complete",
            "state": {
                "profile_result": ProfileAgentResult(
                    reason="测试更新",
                    profile=ProfileData(),
                ),
                "answer": "生成完成",
                "trace": ["测试工作流"],
            },
        }


class InspectingStudioWorkflow:
    """在生成过程中检查数据库事务状态的测试工作流。"""

    def __init__(self, session: AsyncSession):
        """
        初始化Studio测试工作流
        :param session: 数据库会话
        :return:
        """
        self.session = session

    async def run_studio(self, notebook_title, messages, profile, request):
        """
        模拟长时间运行的Studio生成工作流
        :param notebook_title: 笔记本标题
        :param messages: 对话消息
        :param profile: 学生画像
        :param request: 生成请求
        :return:
        """
        assert not self.session.in_transaction()
        return {
            "artifact": {
                "title": "测试产物",
                "content": "测试内容",
                "artifact_data": {},
            },
            "trace": ["测试Studio"],
            "approved": True,
        }


@pytest_asyncio.fixture
async def notebook_db(tmp_path):
    """
    创建笔记本事务测试数据库
    :param tmp_path: pytest临时目录
    :return:
    """
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'test_notebook_transactions.db'}"
    engine = create_async_engine(
        url=database_url,
        connect_args={
            "check_same_thread": False,
            "timeout": 1,
        },
    )
    session_local = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_local() as session:
        user = User(
            username="tester",
            email="tester@example.com",
            hashed_password="hashed",
        )
        notebook = Notebook(
            user_id=1,
            title="测试笔记本",
            description="",
        )
        session.add(user)
        await session.flush()
        notebook.user_id = user.id
        session.add(notebook)
        await session.commit()
        user_id = user.id
        notebook_id = notebook.id

    try:
        yield session_local, user_id, notebook_id
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_stream_chat_releases_database_transaction_while_generating(notebook_db):
    session_local, user_id, notebook_id = notebook_db

    async with session_local() as chat_session, session_local() as note_session:
        user = await chat_session.scalar(select(User).where(User.id == user_id))
        assert user is not None

        workflow = WaitingChatWorkflow()
        chat_service = NotebookService(
            session=chat_session,
            current_user=user,
            workflow=workflow,
        )
        stream = chat_service.stream_chat(
            notebook_id=notebook_id,
            message="请生成学习资料",
        )

        user_event = await stream.__anext__()
        assert user_event["event"] == "user_message"

        status_event = await stream.__anext__()
        assert status_event["event"] == "status"
        assert not chat_session.in_transaction()

        note_service = NotebookService(session=note_session, current_user=user)
        note_result = await note_service.create_note(
            notebook_id=notebook_id,
            request=NotebookNoteCreate(title="并发笔记", content="生成期间保存"),
        )
        assert note_result["errcode"] == 0

        assert workflow.release is not None
        workflow.release.set()
        final_events = [event async for event in stream]
        assert final_events[-1]["event"] == "complete"


@pytest.mark.asyncio
async def test_generate_artifact_releases_read_transaction_before_model_call(notebook_db):
    session_local, user_id, notebook_id = notebook_db

    async with session_local() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        assert user is not None

        service = NotebookService(
            session=session,
            current_user=user,
            workflow=InspectingStudioWorkflow(session=session),
        )
        result = await service.generate_artifact(
            notebook_id=notebook_id,
            request=StudioArtifactGenerate(artifact_type="study_guide"),
        )

        assert result["errcode"] == 0
        assert result["artifact"]["title"] == "测试产物"

        delete_result = await service.delete_artifact(
            notebook_id=notebook_id,
            artifact_id=result["artifact"]["id"],
        )
        assert delete_result == {"errcode": 0}
        artifact = await session.scalar(
            select(StudioArtifact).where(StudioArtifact.id == result["artifact"]["id"]),
        )
        assert artifact is None
