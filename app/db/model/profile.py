# -*- coding: utf-8 -*-
"""学生画像和画像历史版本模型。"""

from typing import Any

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class StudentProfile(Base, TimestampMixin):
    """笔记本内独立维护的学生画像"""

    __tablename__ = "student_profile"

    # id
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 用户id
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)

    # 笔记本id
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebook.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # 专业
    major: Mapped[str] = mapped_column(String(128), nullable=False)

    # 学习目标
    learning_goal: Mapped[str] = mapped_column(Text, nullable=False)

    # 知识基础
    knowledge_level: Mapped[str] = mapped_column(String(128), nullable=False)

    # 薄弱知识点
    weak_points: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # 学习偏好
    learning_style: Mapped[str] = mapped_column(String(128), nullable=False)

    # 可用时间
    available_time: Mapped[str] = mapped_column(String(128), nullable=False)

    # 兴趣方向
    interests: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    # 扩展画像
    profile_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # 版本
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class ProfileRevision(Base, TimestampMixin):
    """笔记本内学生画像历史版本"""

    __tablename__ = "profile_revision"

    # id
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 用户id
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)

    # 笔记本id
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebook.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 画像版本
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # 更新原因
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # 完整画像快照
    profile_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
