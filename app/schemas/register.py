# -*- coding: utf-8 -*-
"""注册请求 Pydantic Schema。"""

from pydantic import BaseModel, Field


class Register(BaseModel):
    """注册模型"""

    username: str = Field(..., description="用户名，唯一")
    password: str = Field(..., description="密码")
    confirm_password: str = Field(..., description="再次确认密码")
    email: str = Field(..., description="邮箱")
    email_code: str = Field(..., min_length=1, description="邮箱验证码")
