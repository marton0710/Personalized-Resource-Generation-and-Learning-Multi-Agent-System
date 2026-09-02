from sqlalchemy.ext.asyncio import AsyncSession

from .artifact import NotebookArtifactRepositoryMixin
from .attachment import NotebookAttachmentRepositoryMixin
from .base import NotebookBaseRepositoryMixin
from .message import NotebookMessageRepositoryMixin
from .note import NotebookNoteRepositoryMixin
from .source import NotebookSourceRepositoryMixin


class NotebookRepositories(
    NotebookBaseRepositoryMixin,
    NotebookAttachmentRepositoryMixin,
    NotebookSourceRepositoryMixin,
    NotebookMessageRepositoryMixin,
    NotebookArtifactRepositoryMixin,
    NotebookNoteRepositoryMixin,
):
    """笔记本工作区数据库操作门面。"""

    def __init__(self, session: AsyncSession):
        """
        初始化笔记本数据库操作
        :param session: 数据库会话
        :return:
        """
        self.session = session
