# -*- coding: utf-8 -*-
"""Studio 学习产物生成智能体门面。"""

from typing import Any

from app.agent.client import DeepSeekClient
from .tools import build_studio_tools
from app.schemas import ProfileData
from app.schemas.notebook import StudioArtifactGenerate


class StudioAgent:
    """根据Studio应用类型按需调用具体产物工具类。"""

    def __init__(self, client: DeepSeekClient | None = None):
        """
        初始化Studio学习产物智能体
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client or DeepSeekClient()
        self.tools = build_studio_tools(client=self.client)

    async def run(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            request: StudioArtifactGenerate,
            review_feedback: str = "",
    ) -> dict[str, Any]:
        """
        调用具体Studio产物工具类生成学习产物
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检改进意见
        :return:
        """
        tool = self.tools[request.artifact_type]
        return await tool.run(
            notebook_title=notebook_title,
            messages=messages,
            profile=profile,
            request=request,
            review_feedback=review_feedback,
        )
