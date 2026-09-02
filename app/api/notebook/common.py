# -*- coding: utf-8 -*-
"""笔记本接口通用错误转换工具。"""

from fastapi import HTTPException

from app.utils import Error


def raise_notebook_http_error(error: Error) -> None:
    """
    将笔记本业务错误转换为HTTP异常
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
