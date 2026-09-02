# -*- coding: utf-8 -*-
"""学生画像数据库操作。"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import ProfileRevision, StudentProfile


class ProfileRepositories:
    """学生画像数据库操作"""

    def __init__(self, session: AsyncSession):
        """
        初始化学生画像数据库操作
        :param session: 数据库会话
        :return:
        """
        self.session = session

    async def get_profile(self, user_id: int, notebook_id: int) -> StudentProfile | None:
        """
        查询指定笔记本内的学生画像
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :return: StudentProfile对象
        """
        stmt = select(StudentProfile).where(
            StudentProfile.user_id == user_id,
            StudentProfile.notebook_id == notebook_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_profile(
            self,
            user_id: int,
            notebook_id: int,
            profile_data: dict[str, Any],
            reason: str,
    ) -> StudentProfile:
        """
        保存学生画像
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :param profile_data: 学生画像数据
        :param reason: 更新原因
        :return: StudentProfile对象
        """
        row = await self.get_profile(user_id=user_id, notebook_id=notebook_id)
        version = 1 if row is None else row.version + 1

        if row is None:
            row = StudentProfile(user_id=user_id, notebook_id=notebook_id)
            self.session.add(row)

        row.major = profile_data["major"]
        row.learning_goal = profile_data["learning_goal"]
        row.knowledge_level = profile_data["knowledge_level"]
        row.weak_points = profile_data["weak_points"]
        row.learning_style = profile_data["learning_style"]
        row.available_time = profile_data["available_time"]
        row.interests = profile_data["interests"]
        row.profile_data = profile_data
        row.version = version

        revision = ProfileRevision(
            user_id=user_id,
            notebook_id=notebook_id,
            version=version,
            reason=reason,
            profile_data=profile_data,
        )
        self.session.add(revision)
        await self.session.flush()
        return row
