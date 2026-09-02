# -*- coding: utf-8 -*-
"""笔记本服务层响应序列化工具。"""

from typing import Any

from app.db.model import (
    Notebook,
    NotebookAttachment,
    NotebookMessage,
    NotebookNote,
    NotebookSource,
    StudentProfile,
    StudioArtifact,
)


def dump_notebook(row: Notebook) -> dict[str, Any]:
    """
    序列化学习笔记本
    :param row: 笔记本对象
    :return:
    """
    return {
        "id": row.id,
        "title": row.title,
        "description": row.description,
        "emoji": row.emoji,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


def dump_attachment(row: NotebookAttachment) -> dict[str, Any]:
    """
    序列化中央对话图片附件
    :param row: 图片附件对象
    :return:
    """
    return {
        "id": row.id,
        "attachment_type": row.attachment_type,
        "original_name": row.original_name,
        "content_type": row.content_type,
        "file_size": row.file_size,
    }


def dump_source(row: NotebookSource) -> dict[str, Any]:
    """
    序列化笔记本PDF知识库来源
    :param row: PDF来源对象
    :return:
    """
    return {
        "id": row.id,
        "original_name": row.original_name,
        "content_type": row.content_type,
        "file_size": row.file_size,
        "page_count": row.page_count,
        "chunk_count": row.chunk_count,
        "text_page_count": row.text_page_count,
        "ocr_page_count": row.ocr_page_count,
        "extraction_method": row.extraction_method,
        "status": row.status,
        "error_message": row.error_message,
        "created_at": row.created_at,
    }


def dump_message(
        row: NotebookMessage,
        attachments: list[NotebookAttachment] | None = None,
) -> dict[str, Any]:
    """
    序列化中央对话消息
    :param row: 对话消息对象
    :param attachments: 消息关联图片附件
    :return:
    """
    return {
        "id": row.id,
        "role": row.role,
        "content": row.content,
        "attachments": [
            dump_attachment(attachment)
            for attachment in attachments or []
        ],
        "created_at": row.created_at,
    }


def dump_artifact(row: StudioArtifact) -> dict[str, Any]:
    """
    序列化Studio学习产物
    :param row: Studio产物对象
    :return:
    """
    return {
        "id": row.id,
        "artifact_type": row.artifact_type,
        "title": row.title,
        "content": row.content,
        "artifact_data": row.artifact_data,
        "custom_prompt": row.custom_prompt,
        "status": row.status,
        "created_at": row.created_at,
    }


def dump_note(row: NotebookNote) -> dict[str, Any]:
    """
    序列化笔记本笔记
    :param row: 笔记对象
    :return:
    """
    return {
        "id": row.id,
        "title": row.title,
        "content": row.content,
        "note_type": row.note_type,
        "created_at": row.created_at,
    }


def dump_profile(row: StudentProfile | None) -> dict[str, Any] | None:
    """
    序列化学生画像
    :param row: 学生画像对象
    :return:
    """
    if row is None:
        return None
    return {
        "id": row.id,
        "version": row.version,
        **row.profile_data,
    }
