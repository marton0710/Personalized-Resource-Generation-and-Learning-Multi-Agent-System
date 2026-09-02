# -*- coding: utf-8 -*-
"""学习笔记本、消息、来源、产物和笔记模型。"""

from typing import Any

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Notebook(Base, TimestampMixin):
    """围绕一个学习主题组织内容的独立笔记本"""

    __tablename__ = "notebook"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    emoji: Mapped[str] = mapped_column(String(16), nullable=False, default="N")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class NotebookMessage(Base, TimestampMixin):
    """笔记本中央对话区消息"""

    __tablename__ = "notebook_message"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebook.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class NotebookAttachment(Base, TimestampMixin):
    """中央对话中随用户消息发送的图片附件"""

    __tablename__ = "notebook_attachment"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebook.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[int | None] = mapped_column(
        ForeignKey("notebook_message.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    attachment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    original_name: Mapped[str] = mapped_column(String(256), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    extracted_content: Mapped[str] = mapped_column(Text, nullable=False)


class NotebookSource(Base, TimestampMixin):
    """笔记本中用户上传的PDF知识库来源"""

    __tablename__ = "notebook_source"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebook.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    original_name: Mapped[str] = mapped_column(String(256), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)
    page_count: Mapped[int] = mapped_column(nullable=False, default=0)
    chunk_count: Mapped[int] = mapped_column(nullable=False, default=0)
    text_page_count: Mapped[int] = mapped_column(nullable=False, default=0)
    ocr_page_count: Mapped[int] = mapped_column(nullable=False, default=0)
    extraction_method: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    qdrant_collection: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="processing")
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")


class StudioArtifact(Base, TimestampMixin):
    """Studio按需生成的学习产物"""

    __tablename__ = "studio_artifact"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebook.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    custom_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ready")


class NotebookNote(Base, TimestampMixin):
    """用户编写或从对话保存的笔记"""

    __tablename__ = "notebook_note"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    notebook_id: Mapped[int] = mapped_column(
        ForeignKey("notebook.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
