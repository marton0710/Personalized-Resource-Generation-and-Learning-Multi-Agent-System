# -*- coding: utf-8 -*-
"""当前登录用户鉴权依赖。"""

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import User
from app.db.repositories import UserRepositories
from app.db.session import get_session
from app.utils import Error, get_token_identity

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: AsyncSession = Depends(get_session),
) -> User:
    """
    获取当前登录用户，路由守卫
    :param token: jwt token
    :param session: 数据库会话
    :return:
    """
    try:
        sub, session_id = get_token_identity(token)
    except Error as e:
        raise HTTPException(
            status_code=401,
            detail={"code": e.code, "message": e.message},
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepositories(session=session)
    row = await repo.get_user_by_username(username=sub)
    if row is None or row.active_session_id != session_id:
        raise HTTPException(
            status_code=401,
            detail={"code": 401, "message": "登录已失效，请重新登录"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    return row
