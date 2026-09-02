# -*- coding: utf-8 -*-
"""笔记本主表数据库操作。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import Notebook


class NotebookBaseRepositoryMixin:
    """笔记本主表数据库操作。"""

    session: AsyncSession

    async def create_notebook(self, user_id: int, title: str, description: str = "") -> Notebook:
        """
        创建学习笔记本
        :param user_id: 用户id
        :param title: 笔记本标题
        :param description: 学习说明
        :return:
        """
        row = Notebook(
            user_id=user_id,
            title=title,
            description=description,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_notebooks(self, user_id: int) -> list[Notebook]:
        """
        查询用户的学习笔记本
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(Notebook)
            .where(
                Notebook.user_id == user_id,
                Notebook.status == "active",
            )
            .order_by(Notebook.id.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_notebook(self, notebook_id: int, user_id: int) -> Notebook | None:
        """
        查询用户的指定学习笔记本
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(Notebook)
            .where(
                Notebook.id == notebook_id,
                Notebook.user_id == user_id,
                Notebook.status == "active",
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_notebook(self, notebook: Notebook) -> None:
        """
        删除学习笔记本
        :param notebook: 笔记本对象
        :return:
        """
        await self.session.delete(notebook)
        await self.session.flush()
