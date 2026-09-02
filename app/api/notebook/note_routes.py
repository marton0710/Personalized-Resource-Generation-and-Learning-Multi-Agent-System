# -*- coding: utf-8 -*-
"""笔记本笔记创建、保存和删除接口路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from .common import raise_notebook_http_error
from app.db.model import User
from app.db.session import get_session
from app.schemas.notebook import NotebookNoteCreate, NotebookNoteFromMessage
from app.service.notebook import NotebookService
from app.utils import Error

router = APIRouter()


@router.post("/{notebook_id}/notes")
async def create_notebook_note(
        notebook_id: int,
        resp: NotebookNoteCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    创建笔记本手动笔记
    :param notebook_id: 笔记本id
    :param resp: 创建笔记请求
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.create_note(
            notebook_id=notebook_id,
            request=resp,
        )
    except Error as e:
        raise_notebook_http_error(e)


@router.post("/{notebook_id}/notes/from-message")
async def save_notebook_message_as_note(
        notebook_id: int,
        resp: NotebookNoteFromMessage,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    将辅导回复保存为笔记
    :param notebook_id: 笔记本id
    :param resp: 消息转笔记请求
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.save_message_as_note(
            notebook_id=notebook_id,
            message_id=resp.message_id,
        )
    except Error as e:
        raise_notebook_http_error(e)


@router.delete("/{notebook_id}/notes/{note_id}")
async def delete_notebook_note(
        notebook_id: int,
        note_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    删除笔记本笔记
    :param notebook_id: 笔记本id
    :param note_id: 笔记id
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.delete_note(notebook_id=notebook_id, note_id=note_id)
    except Error as e:
        raise_notebook_http_error(e)
