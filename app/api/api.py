# -*- coding: utf-8 -*-
"""FastAPI 总路由与认证相关接口。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.forum import router as forum_router
from app.api.notebook import router as notebook_router
from app.db.model import User
from app.db.session import get_session
from app.schemas import (
    EmailCodeLogin,
    EmailCodeRequest,
    Login,
    Register,
    UserSignatureUpdate,
)
from app.service import UserService
from app.utils import Error

router = APIRouter(prefix="/api")
router.include_router(forum_router)
router.include_router(notebook_router)


def _raise_http_error(error: Error) -> None:
    """
    将业务错误转换为HTTP异常
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


@router.post("/auth/login")
async def login(
        resp: Login,
        session: AsyncSession = Depends(get_session),
):
    """
    登录并返回访问令牌
    :param resp: 登录请求
    :param session: 数据库会话
    :return:
    """
    service = UserService(
        session=session,
        username=resp.username,
        password=resp.password,
    )
    try:
        access_token = await service.login()
        return {
            "errcode": 0,
            "username": resp.username,
            "token": access_token,
        }
    except Error as e:
        _raise_http_error(e)


@router.post("/auth/login/email")
async def login_by_email_code(
        resp: EmailCodeLogin,
        session: AsyncSession = Depends(get_session),
):
    """
    邮箱验证码登录并返回访问令牌
    :param resp: 邮箱验证码登录请求
    :param session: 数据库会话
    :return:
    """
    service = UserService(
        session=session,
        email=resp.email,
        email_code=resp.email_code,
    )
    try:
        access_token = await service.login_by_email_code()
        return {
            "errcode": 0,
            "email": resp.email,
            "token": access_token,
        }
    except Error as e:
        _raise_http_error(e)


@router.post("/auth/email-code")
async def send_email_code(
        resp: EmailCodeRequest,
        session: AsyncSession = Depends(get_session),
):
    """
    发送邮箱验证码
    :param resp: 邮箱验证码发送请求
    :param session: 数据库会话
    :return:
    """
    service = UserService(
        session=session,
        email=resp.email,
    )
    try:
        expires_in = await service.send_email_code(purpose=resp.purpose)
        return {
            "errcode": 0,
            "email": resp.email,
            "expires_in": expires_in,
        }
    except Error as e:
        _raise_http_error(e)


@router.post("/auth/register")
async def register(
        resp: Register,
        session: AsyncSession = Depends(get_session),
):
    """
    注册新用户
    :param resp: 注册请求
    :param session: 数据库会话
    :return:
    """
    service = UserService(
        session=session,
        username=resp.username,
        password=resp.password,
        confirm_password=resp.confirm_password,
        email=resp.email,
        email_code=resp.email_code,
    )
    try:
        username = await service.add_new_user()
        return {
            "errcode": 0,
            "username": username,
        }
    except Error as e:
        _raise_http_error(e)


@router.get("/auth/me")
async def get_me(
        current_user: User = Depends(get_current_user),
):
    """
    获取当前登录用户
    :param current_user: 当前登录用户
    :return:
    """
    return {
        "errcode": 0,
        "username": current_user.username,
        "nickname": current_user.username,
        "email": current_user.email,
        "signature": current_user.signature,
    }


@router.put("/auth/me/signature")
async def update_signature(
        resp: UserSignatureUpdate,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    """
    更新当前用户个性签名
    :param resp: 个性签名请求
    :param current_user: 当前登录用户
    :param session: 数据库会话
    :return:
    """
    service = UserService(session=session)
    try:
        signature = await service.update_signature(
            row=current_user,
            signature=resp.signature,
        )
        return {
            "errcode": 0,
            "username": current_user.username,
            "nickname": current_user.username,
            "email": current_user.email,
            "signature": signature,
        }
    except Error as e:
        _raise_http_error(e)
