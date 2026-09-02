# -*- coding: utf-8 -*-
"""学习论坛接口路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db.model import User
from app.db.session import get_session
from app.schemas.forum import ForumCommentCreate, ForumPostCreate
from app.service.forum import ForumService
from app.utils import Error

router = APIRouter(prefix="/forum", tags=["forum"])


def _raise_http_error(error: Error) -> None:
    """
    将论坛业务错误转换为HTTP异常
    :param error: 业务错误
    :return:
    """
    raise HTTPException(
        status_code=error.code,
        detail={
            "code": error.code,
            "message": error.message,
        },
    )


@router.post("/posts")
async def create_forum_post(
        resp: ForumPostCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    创建论坛帖子
    :param resp: 创建帖子请求
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = ForumService(session=session, current_user=current_user)
    return await service.create_post(
        title=resp.title,
        content=resp.content,
        category=resp.category,
    )


@router.get("/posts")
async def list_forum_posts(
        category: str = Query(default="", max_length=64),
        keyword: str = Query(default="", max_length=256),
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    查询论坛帖子列表
    :param category: 讨论分区
    :param keyword: 搜索关键词
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = ForumService(session=session, current_user=current_user)
    return await service.list_posts(category=category, keyword=keyword)


@router.get("/posts/{post_id}")
async def get_forum_post(
        post_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    获取论坛帖子详情
    :param post_id: 帖子id
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = ForumService(session=session, current_user=current_user)
    try:
        return await service.get_post(post_id=post_id)
    except Error as e:
        _raise_http_error(e)


@router.delete("/posts/{post_id}")
async def delete_forum_post(
        post_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    删除当前用户发布的论坛帖子
    :param post_id: 帖子id
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = ForumService(session=session, current_user=current_user)
    try:
        return await service.delete_post(post_id=post_id)
    except Error as e:
        _raise_http_error(e)


@router.post("/posts/{post_id}/comments")
async def create_forum_comment(
        post_id: int,
        resp: ForumCommentCreate,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    创建论坛帖子评论
    :param post_id: 帖子id
    :param resp: 创建评论请求
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = ForumService(session=session, current_user=current_user)
    try:
        return await service.create_comment(post_id=post_id, content=resp.content)
    except Error as e:
        _raise_http_error(e)


@router.post("/posts/{post_id}/like")
async def toggle_forum_post_like(
        post_id: int,
        session: AsyncSession = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    切换论坛帖子点赞状态
    :param post_id: 帖子id
    :param session: 数据库会话
    :param current_user: 当前登录用户
    :return:
    """
    service = ForumService(session=session, current_user=current_user)
    try:
        return await service.toggle_like(post_id=post_id)
    except Error as e:
        _raise_http_error(e)
