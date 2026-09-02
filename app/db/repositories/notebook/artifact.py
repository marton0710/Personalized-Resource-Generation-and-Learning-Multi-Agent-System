# -*- coding: utf-8 -*-
"""笔记本 Studio 产物数据库操作。"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import StudioArtifact


class NotebookArtifactRepositoryMixin:
    """Studio学习产物数据库操作。"""

    session: AsyncSession

    async def create_artifact(
            self,
            user_id: int,
            notebook_id: int,
            artifact_type: str,
            title: str,
            content: str,
            artifact_data: dict[str, Any],
            custom_prompt: str,
    ) -> StudioArtifact:
        """
        创建Studio学习产物
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :param artifact_type: 产物类型
        :param title: 产物标题
        :param content: 产物正文
        :param artifact_data: 结构化产物数据
        :param custom_prompt: 用户补充要求
        :return:
        """
        row = StudioArtifact(
            user_id=user_id,
            notebook_id=notebook_id,
            artifact_type=artifact_type,
            title=title,
            content=content,
            artifact_data=artifact_data,
            custom_prompt=custom_prompt,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_artifacts(self, notebook_id: int, user_id: int) -> list[StudioArtifact]:
        """
        查询笔记本中的Studio学习产物
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(StudioArtifact)
            .where(
                StudioArtifact.notebook_id == notebook_id,
                StudioArtifact.user_id == user_id,
            )
            .order_by(StudioArtifact.id.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_artifact(
            self,
            artifact_id: int,
            notebook_id: int,
            user_id: int,
    ) -> StudioArtifact | None:
        """
        查询笔记本中的指定Studio学习产物
        :param artifact_id: 产物id
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        stmt = select(StudioArtifact).where(
            StudioArtifact.id == artifact_id,
            StudioArtifact.notebook_id == notebook_id,
            StudioArtifact.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_artifact(self, artifact: StudioArtifact) -> None:
        """
        删除Studio学习产物
        :param artifact: Studio产物对象
        :return:
        """
        await self.session.delete(artifact)
        await self.session.flush()
