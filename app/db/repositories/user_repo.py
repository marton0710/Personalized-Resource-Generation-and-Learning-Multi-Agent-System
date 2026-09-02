# -*- coding: utf-8 -*-
"""用户账号数据库操作。"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import User


class UserRepositories:
    """user数据库操作"""

    def __init__(self, session: AsyncSession):
        """
        初始化user数据库操作
        :param session: 数据库会话
        :return:
        """
        self.session = session

    async def create_user(
            self,
            username: str,
            password: str,
            email: str,
    ) -> User:
        """
        新建user
        :param username: 用户名
        :param password: 密码
        :param email: 邮箱
        :return: User对象
        """
        new_user = User(
            username=username,
            hashed_password=password,
            email=email,
        )
        self.session.add(new_user)
        await self.session.flush()
        return new_user

    async def get_user_by_username(self, username: str) -> User | None:
        """
        仅通过username查询用户
        :param username: 用户名
        :return: User对象
        """
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        仅通过email查询用户
        :param email: 邮箱
        :return: User对象
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username_or_by_email(self, username: str, email: str) -> User | None:
        """
        通过username或email查询用户
        :param username: 用户名
        :param email: 邮箱
        :return: User对象
        """
        stmt = (
            select(User)
            .where(
                or_(
                    User.username == username,
                    User.email == email,
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
