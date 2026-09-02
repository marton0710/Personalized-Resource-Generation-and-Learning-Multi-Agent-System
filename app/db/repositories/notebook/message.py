# -*- coding: utf-8 -*-
"""笔记本中央对话消息数据库操作。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import NotebookMessage


class NotebookMessageRepositoryMixin:
    """中央对话消息数据库操作。"""

    session: AsyncSession

    async def create_message(self, notebook_id: int, role: str, content: str) -> NotebookMessage:
        """
        创建中央对话消息
        :param notebook_id: 笔记本id
        :param role: 消息角色
        :param content: 消息正文
        :return:
        """
        row = NotebookMessage(
            notebook_id=notebook_id,
            role=role,
            content=content,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_messages(self, notebook_id: int, limit: int = 30) -> list[NotebookMessage]:
        """
        查询笔记本最近的中央对话消息
        :param notebook_id: 笔记本id
        :param limit: 最大返回数量
        :return:
        """
        stmt = (
            select(NotebookMessage)
            .where(NotebookMessage.notebook_id == notebook_id)
            .order_by(NotebookMessage.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(reversed(result.scalars().all()))

    async def get_message(self, message_id: int, notebook_id: int) -> NotebookMessage | None:
        """
        查询笔记本中的指定消息
        :param message_id: 消息id
        :param notebook_id: 笔记本id
        :return:
        """
        stmt = (
            select(NotebookMessage)
            .where(
                NotebookMessage.id == message_id,
                NotebookMessage.notebook_id == notebook_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
