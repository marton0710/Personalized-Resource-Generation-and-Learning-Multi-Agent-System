# -*- coding: utf-8 -*-
"""笔记本手动笔记数据库操作。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import NotebookNote


class NotebookNoteRepositoryMixin:
    """笔记本手动笔记数据库操作。"""

    session: AsyncSession

    async def create_note(
            self,
            user_id: int,
            notebook_id: int,
            title: str,
            content: str,
            note_type: str = "manual",
    ) -> NotebookNote:
        """
        创建笔记本笔记
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :param title: 笔记标题
        :param content: 笔记正文
        :param note_type: 笔记类型
        :return:
        """
        row = NotebookNote(
            user_id=user_id,
            notebook_id=notebook_id,
            title=title,
            content=content,
            note_type=note_type,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_notes(self, notebook_id: int, user_id: int) -> list[NotebookNote]:
        """
        查询笔记本笔记列表
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(NotebookNote)
            .where(
                NotebookNote.notebook_id == notebook_id,
                NotebookNote.user_id == user_id,
            )
            .order_by(NotebookNote.id.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_note(
            self,
            note_id: int,
            notebook_id: int,
            user_id: int,
    ) -> NotebookNote | None:
        """
        查询笔记本中的指定笔记
        :param note_id: 笔记id
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        stmt = select(NotebookNote).where(
            NotebookNote.id == note_id,
            NotebookNote.notebook_id == notebook_id,
            NotebookNote.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_note(self, note: NotebookNote) -> None:
        """
        删除笔记本笔记
        :param note: 笔记对象
        :return:
        """
        await self.session.delete(note)
        await self.session.flush()
