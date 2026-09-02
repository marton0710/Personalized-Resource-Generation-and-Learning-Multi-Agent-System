# -*- coding: utf-8 -*-
"""应用启动时的数据库建表和兼容初始化。"""

from sqlalchemy import Connection, inspect, text

from app.db.base import Base
from app.db.engine import engine

import app.db.model  # noqa: F401


def _drop_legacy_user_scoped_profile_tables(conn: Connection) -> None:
    """
    首次升级时移除无法归属到具体笔记本的旧画像表
    :param conn: 数据库连接
    :return:
    """
    inspector = inspect(conn)
    if "student_profile" not in inspector.get_table_names():
        return
    columns = {
        column["name"]
        for column in inspector.get_columns("student_profile")
    }
    if "notebook_id" in columns:
        return
    conn.execute(text("DROP TABLE IF EXISTS profile_revision"))
    conn.execute(text("DROP TABLE student_profile"))


def _ensure_active_session_id_column(conn: Connection) -> None:
    """
    为已有SQLite数据库补充单会话登录字段
    :param conn: 数据库连接
    :return:
    """
    columns = {
        column["name"]
        for column in inspect(conn).get_columns("user")
    }
    if "active_session_id" not in columns:
        conn.execute(text(
            'ALTER TABLE "user" ADD COLUMN active_session_id VARCHAR(64)'
        ))


def _ensure_signature_column(conn: Connection) -> None:
    """
    为已有SQLite数据库补充个性签名字段
    :param conn: 数据库连接
    :return:
    """
    columns = {
        column["name"]
        for column in inspect(conn).get_columns("user")
    }
    if "signature" not in columns:
        conn.execute(text(
            "ALTER TABLE \"user\" ADD COLUMN signature VARCHAR(200) NOT NULL DEFAULT ''"
        ))


async def init_db() -> None:
    """
    初始化数据库表
    :return:
    """
    async with engine.begin() as conn:
        await conn.run_sync(_drop_legacy_user_scoped_profile_tables)
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_active_session_id_column)
        await conn.run_sync(_ensure_signature_column)
