# -*- coding: utf-8 -*-
"""异步数据库会话工厂和 FastAPI 依赖。"""

from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.engine import engine


# 全局会话工厂：业务代码里按需拿session
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    :return: 数据库会话生成器
    """

    async with SessionLocal() as session:
        yield session
