# -*- coding: utf-8 -*-
"""个性化学习路径规划智能体。"""

import json

from app.agent.client import DeepSeekClient
from app.schemas import LearningPathData, ProfileData


class LearningPathAgent:
    """个性化学习路径智能体"""

    def __init__(self, client: DeepSeekClient | None = None):
        """
        初始化个性化学习路径智能体
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client or DeepSeekClient()

    async def run(self, profile: ProfileData, course_topic: str) -> LearningPathData:
        """
        生成学习路径
        :param profile: 学生画像
        :param course_topic: 课程主题
        :return:
        """
        system_prompt = """
你是学习路径规划智能体。请根据学生画像，为课程主题规划由浅入深的学习路径。
你必须输出合法json，不要输出json以外的文本。
steps生成3到6个步骤，每个步骤包含title、knowledge_point和reason。
不要假设存在外部知识库，不要生成虚假的参考资料。
输出json格式示例：
{
  "title": "Python循环个性化学习路径",
  "steps": [
    {
      "title": "理解循环基础",
      "knowledge_point": "for与while循环",
      "reason": "先建立基础概念"
    }
  ]
}
"""
        user_prompt = (
            f"课程主题：{course_topic}\n"
            "学生画像：\n"
            f"{json.dumps(profile.model_dump(mode='json'), ensure_ascii=False)}"
        )
        payload = await self.client.json_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1600,
        )
        return LearningPathData.model_validate(payload)
