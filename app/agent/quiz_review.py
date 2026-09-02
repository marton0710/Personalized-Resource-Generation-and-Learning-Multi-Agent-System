# -*- coding: utf-8 -*-
"""测验复盘与画像更新智能体。"""

import json
from typing import Any

from app.agent.client import DeepSeekClient
from app.schemas import QuizReviewAgentResult


class QuizReviewAgent:
    """根据测验结果生成点评并更新学生画像。"""

    def __init__(self, client: DeepSeekClient | None = None):
        """
        初始化测验复盘画像智能体
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client or DeepSeekClient()

    async def run(
            self,
            notebook_title: str,
            quiz_title: str,
            current_profile: dict[str, Any],
            attempt_summary: dict[str, Any],
    ) -> QuizReviewAgentResult:
        """
        根据完整测验作答结果生成点评和画像更新
        :param notebook_title: 笔记本标题
        :param quiz_title: 测验标题
        :param current_profile: 当前学生画像
        :param attempt_summary: 测验作答摘要
        :return:
        """
        system_prompt = """
你是测验复盘与画像更新智能体。请根据学生一次完整测验的作答结果，输出合法JSON，不要输出JSON以外的文本。

你的任务有两个：
1. 给学生一段测验点评：先给整体判断，再指出主要掌握点、薄弱点和下一步建议。
2. 基于本次测验证据更新七维学习画像：专业、学习目标、知识基础、薄弱知识点、学习偏好、可用时间、兴趣方向。

要求：
- 点评要直接、克制、结构清晰，不做夸张表扬，也不要把一次测验过度解读成长期能力结论。
- 只根据当前画像和本次测验结果更新学习相关字段；证据不足的字段保持原值或“待补充”。
- 薄弱点优先来自答错题涉及的概念；如果全对，可以保留已有薄弱点，或根据题目范围给出“需要继续巩固”的具体方向。
- 不要编造学生没有表达过的专业、时间安排和兴趣方向。

输出JSON格式：
{
  "reason": "本次画像更新原因",
  "review": "给学生看的测验点评，使用简洁Markdown",
  "profile": {
    "major": "待补充",
    "learning_goal": "待补充",
    "knowledge_level": "待补充",
    "weak_points": [],
    "learning_style": "待补充",
    "available_time": "待补充",
    "interests": [],
    "extra_data": {}
  }
}
"""
        user_prompt = (
            f"当前笔记本：{notebook_title}\n"
            f"测验标题：{quiz_title}\n"
            "当前画像：\n"
            f"{json.dumps(current_profile or {}, ensure_ascii=False)}\n"
            "完整测验作答摘要：\n"
            f"{json.dumps(attempt_summary, ensure_ascii=False)}"
        )
        payload = await self.client.json_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1600,
        )
        return QuizReviewAgentResult.model_validate(payload)
