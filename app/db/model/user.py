# -*- coding: utf-8 -*-
"""用户账号 SQLAlchemy 模型。"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    """存储user数据库模型"""

    __tablename__ = "user"

    # id
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 用户名
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    # 密码
    hashed_password: Mapped[str] = mapped_column(String(1024), nullable=False)

    # 邮箱
    email: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    # 个性签名
    signature: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    # 当前有效登录会话；新登录会覆盖旧会话
    active_session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
