# -*- coding: utf-8 -*-
"""登录请求 Pydantic Schema。"""

from typing import Literal

from pydantic import BaseModel, Field


class Login(BaseModel):
    """登录模型"""

    username: str = Field(..., description="用户名，唯一")
    password: str = Field(..., description="密码")


class EmailCodeRequest(BaseModel):
    """邮箱验证码发送模型"""

    email: str = Field(..., description="邮箱")
    purpose: Literal["login", "register"] = Field(..., description="验证码用途")


class EmailCodeLogin(BaseModel):
    """邮箱验证码登录模型"""

    email: str = Field(..., description="邮箱")
    email_code: str = Field(..., min_length=1, description="邮箱验证码")


class UserSignatureUpdate(BaseModel):
    """用户个性签名更新模型"""

    signature: str = Field("", max_length=200, description="个性签名")
