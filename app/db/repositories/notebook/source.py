# -*- coding: utf-8 -*-
"""笔记本 PDF 来源数据库操作。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import NotebookSource


class NotebookSourceRepositoryMixin:
    """笔记本PDF来源数据库操作。"""

    session: AsyncSession

    async def create_source(
            self,
            notebook_id: int,
            user_id: int,
            original_name: str,
            stored_path: str,
            content_type: str,
            file_size: int,
            qdrant_collection: str,
    ) -> NotebookSource:
        """
        创建笔记本PDF来源记录
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :param original_name: 原始文件名
        :param stored_path: 磁盘存储路径
        :param content_type: MIME类型
        :param file_size: 文件大小
        :param qdrant_collection: 用户笔记本Qdrant collection
        :return:
        """
        row = NotebookSource(
            notebook_id=notebook_id,
            user_id=user_id,
            original_name=original_name,
            stored_path=stored_path,
            content_type=content_type,
            file_size=file_size,
            qdrant_collection=qdrant_collection,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def count_sources(self, notebook_id: int, user_id: int) -> int:
        """
        统计笔记本中的PDF来源数量
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(func.count(NotebookSource.id))
            .where(
                NotebookSource.notebook_id == notebook_id,
                NotebookSource.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_sources(self, notebook_id: int, user_id: int) -> list[NotebookSource]:
        """
        查询笔记本PDF来源
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(NotebookSource)
            .where(
                NotebookSource.notebook_id == notebook_id,
                NotebookSource.user_id == user_id,
            )
            .order_by(NotebookSource.id.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_source(
            self,
            source_id: int,
            notebook_id: int,
            user_id: int,
    ) -> NotebookSource | None:
        """
        查询笔记本中的指定PDF来源
        :param source_id: 来源id
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(NotebookSource)
            .where(
                NotebookSource.id == source_id,
                NotebookSource.notebook_id == notebook_id,
                NotebookSource.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_source_paths(self, notebook_id: int) -> list[str]:
        """
        查询笔记本PDF来源的磁盘路径
        :param notebook_id: 笔记本id
        :return:
        """
        stmt = (
            select(NotebookSource.stored_path)
            .where(NotebookSource.notebook_id == notebook_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_source(self, source: NotebookSource) -> None:
        """
        删除PDF来源记录
        :param source: 来源对象
        :return:
        """
        await self.session.delete(source)
        await self.session.flush()
