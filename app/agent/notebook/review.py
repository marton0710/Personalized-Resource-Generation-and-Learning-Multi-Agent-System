# -*- coding: utf-8 -*-
"""Studio 学习产物内容质检智能体。"""

import json
from typing import Any

from app.agent.client import DeepSeekClient
from app.schemas import ProfileData


class ContentReviewAgent:
    """检查Studio产物的质量、安全性和个性化程度。"""

    def __init__(self, client: DeepSeekClient | None = None):
        """
        初始化学习资源质检智能体
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client or DeepSeekClient()

    async def run(
            self,
            artifact_type: str,
            title: str,
            content: str,
            artifact_data: dict[str, Any],
            profile: ProfileData,
    ) -> dict[str, Any]:
        """
        检查Studio学习产物质量
        :param artifact_type: 产物类型
        :param title: 标题
        :param content: 正文
        :param artifact_data: 结构化产物数据
        :param profile: 学生画像
        :return:
        """
        system_prompt = """
你是学习资源质检智能体。请检查待发布的学习产物是否适合交给学生。
检查维度：
1. 内容是否围绕主题且结构完整；
2. 是否体现学生画像中的基础、目标或偏好；
3. 是否存在没有明确依据的来源、页码、链接，或夸大已经读取资料的表述；
4. 是否存在明显事实错误、危险内容或不适合学习场景的表达；
5. 测验和闪卡等结构化内容是否具备可用数据。
必须输出合法json，不要输出json以外的文本。
json格式：
{
  "approved": true,
  "feedback": "通过，或说明需要怎样修正"
}
"""
        payload = await self.client.json_completion(
            system_prompt=system_prompt,
            user_prompt=(
                f"产物类型：{artifact_type}\n"
                f"标题：{title}\n"
                f"学生画像：{json.dumps(profile.model_dump(mode='json'), ensure_ascii=False)}\n"
                f"正文：{content}\n"
                f"结构化数据：{json.dumps(artifact_data, ensure_ascii=False)}"
            ),
            max_tokens=600,
        )
        return {
            "approved": bool(payload.get("approved")),
            "feedback": str(payload.get("feedback") or "质检未提供反馈"),
        }
