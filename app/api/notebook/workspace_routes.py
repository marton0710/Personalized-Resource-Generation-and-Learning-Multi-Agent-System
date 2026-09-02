# -*- coding: utf-8 -*-
"""笔记本创建、列表、工作区详情和删除接口路由。"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from .common import raise_notebook_http_error
from app.db.model import User
from app.db.session import get_session
from app.schemas.notebook import NotebookCreate
from app.service.notebook import NotebookService
from app.utils import Error

router = APIRouter()


@router.post("")
async def create_notebook(
        resp: NotebookCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    创建学习笔记本
    :param resp: 创建笔记本请求
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.create_notebook(
            title=resp.title,
            description=resp.description,
        )
    except Error as e:
        raise_notebook_http_error(e)


@router.get("")
async def list_notebooks(
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    查询当前用户的学习笔记本
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    return await service.list_notebooks()


@router.get("/{notebook_id}")
async def get_notebook_workspace(
        notebook_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    获取学习笔记本工作区
    :param notebook_id: 笔记本id
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.get_workspace(notebook_id=notebook_id)
    except Error as e:
        raise_notebook_http_error(e)


@router.delete("/{notebook_id}")
async def delete_notebook(
        notebook_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    删除学习笔记本
    :param notebook_id: 笔记本id
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = NotebookService(session=session, current_user=current_user)
    try:
        return await service.delete_notebook(notebook_id=notebook_id)
    except Error as e:
        raise_notebook_http_error(e)
