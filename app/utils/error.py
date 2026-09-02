# -*- coding: utf-8 -*-
"""业务异常类型定义。"""

class Error(Exception):
    """业务异常，供服务层抛出并由接口层转换为HTTP错误"""

    def __init__(self, code: int, message: str):
        """
        自定义错误
        :param code: 错误码
        :param message: 错误消息
        :return:
        """
        self.code = code
        self.message = message
        super().__init__(message)
