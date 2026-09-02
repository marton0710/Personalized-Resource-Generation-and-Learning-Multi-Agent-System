# -*- coding: utf-8 -*-
"""千问视觉模型客户端，用于图片预解析。"""

import base64

from openai import AsyncOpenAI

from app.core import settings
from app.utils import Error


class VisionClient:
    """OpenAI兼容视觉模型客户端"""

    def __init__(self):
        """
        初始化OpenAI兼容视觉模型客户端
        :return:
        """
        if not settings.VISION_APIKEY or not settings.vision_model:
            raise Error(
                code=503,
                message="图片上传需要先配置VISION_APIKEY和VISION_MODEL",
            )

        self.client = AsyncOpenAI(
            api_key=settings.VISION_APIKEY,
            base_url=settings.vision_base_url,
        )
        self.model = settings.vision_model

    async def describe_image(self, content: bytes, content_type: str) -> str:
        """
        提取图片中的文字和学习相关视觉信息
        :param content: 图片二进制
        :param content_type: 图片MIME类型
        :return:
        """
        image_data = base64.b64encode(content).decode("ascii")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是学习资料图片解析助手。请准确提取图片中可读的文字、公式、"
                            "表格和图示信息，并简洁描述与学习问题相关的视觉内容。"
                            "不要猜测图片中不存在的信息。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "请解析这张学习资料图片，输出可供后续学习辅导智能体使用的文本说明。",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{content_type};base64,{image_data}",
                                },
                            },
                        ],
                    },
                ],
                max_tokens=1200,
            )
            result = response.choices[0].message.content
            if not result:
                raise Error(code=502, message="视觉模型返回内容为空")
            return result
        except Error:
            raise
        except Exception as e:
            raise Error(code=502, message=f"图片解析失败：{e}") from e
