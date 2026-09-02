# -*- coding: utf-8 -*-
"""笔记本图片附件和 PDF 来源文件接口路由。"""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from .common import raise_notebook_http_error
from app.core import settings
from app.db.model import User
from app.db.session import get_session
from app.service.notebook import NotebookService
from app.utils import Error

router = APIRouter()


@router.post("/{notebook_id}/attachments")
async def upload_notebook_attachment(
        notebook_id: int,
        file: UploadFile = File(...),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    上传中央对话图片附件
    :param notebook_id: 笔记本id
    :param file: 图片文件
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        content = await file.read(settings.chat_attachment_max_bytes + 1)
        return await service.upload_attachment(
            notebook_id=notebook_id,
            filename=file.filename or "",
            content_type=file.content_type or "application/octet-stream",
            content=content,
        )
    except Error as e:
        raise_notebook_http_error(e)
    finally:
        await file.close()


@router.delete("/{notebook_id}/attachments/{attachment_id}")
async def delete_notebook_attachment(
        notebook_id: int,
        attachment_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    删除尚未发送的中央对话图片附件
    :param notebook_id: 笔记本id
    :param attachment_id: 图片附件id
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.delete_attachment(
            notebook_id=notebook_id,
            attachment_id=attachment_id,
        )
    except Error as e:
        raise_notebook_http_error(e)


@router.post("/{notebook_id}/sources")
async def upload_notebook_source(
        notebook_id: int,
        file: UploadFile = File(...),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    上传笔记本PDF知识库来源
    :param notebook_id: 笔记本id
    :param file: PDF文件
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        content = await file.read(settings.knowledge_pdf_max_bytes + 1)
        return await service.upload_source(
            notebook_id=notebook_id,
            filename=file.filename or "",
            content_type=file.content_type or "application/octet-stream",
            content=content,
        )
    except Error as e:
        raise_notebook_http_error(e)
    finally:
        await file.close()


@router.delete("/{notebook_id}/sources/{source_id}")
async def delete_notebook_source(
        notebook_id: int,
        source_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    删除单个笔记本PDF知识库来源
    :param notebook_id: 笔记本id
    :param source_id: 来源id
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.delete_source(
            notebook_id=notebook_id,
            source_id=source_id,
        )
    except Error as e:
        raise_notebook_http_error(e)
