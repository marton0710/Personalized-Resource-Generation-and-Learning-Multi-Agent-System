# -*- coding: utf-8 -*-
"""学习论坛请求 Pydantic Schema。"""

from pydantic import BaseModel, Field


class ForumPostCreate(BaseModel):
    """创建论坛帖子请求"""

    title: str = Field(..., min_length=1, max_length=256)
    content: str = Field(..., min_length=1, max_length=20000)
    category: str = Field(default="交流讨论", min_length=1, max_length=64)


class ForumCommentCreate(BaseModel):
    """创建论坛评论请求"""

    content: str = Field(..., min_length=1, max_length=4000)
