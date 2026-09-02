# -*- coding: utf-8 -*-
"""学习论坛相关 SQLAlchemy 模型。"""

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ForumPost(Base, TimestampMixin):
    """论坛帖子"""

    __tablename__ = "forum_post"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="交流讨论")
    view_count: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class ForumComment(Base, TimestampMixin):
    """论坛帖子评论"""

    __tablename__ = "forum_comment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("forum_post.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class ForumPostLike(Base, TimestampMixin):
    """论坛帖子点赞记录"""

    __tablename__ = "forum_post_like"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_forum_post_like_post_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("forum_post.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
