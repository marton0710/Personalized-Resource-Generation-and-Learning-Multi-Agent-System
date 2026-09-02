# -*- coding: utf-8 -*-
"""智能体结构化输出 Pydantic Schema。"""

from typing import Any

from pydantic import BaseModel, Field


class ProfileData(BaseModel):
    """学生画像数据"""

    major: str = Field(default="待补充", description="专业")
    learning_goal: str = Field(default="待补充", description="学习目标")
    knowledge_level: str = Field(default="待补充", description="知识基础")
    weak_points: list[str] = Field(default_factory=list, description="薄弱知识点")
    learning_style: str = Field(default="待补充", description="学习偏好")
    available_time: str = Field(default="待补充", description="可用时间")
    interests: list[str] = Field(default_factory=list, description="兴趣方向")
    extra_data: dict[str, Any] = Field(default_factory=dict, description="扩展画像")


class ProfileAgentResult(BaseModel):
    """画像智能体输出"""

    reason: str = Field(..., description="本次画像更新原因")
    profile: ProfileData


class QuizReviewAgentResult(BaseModel):
    """测验复盘画像智能体输出"""

    reason: str = Field(..., description="本次画像更新原因")
    review: str = Field(..., description="给学生的测验点评")
    profile: ProfileData


class LearningPathStepData(BaseModel):
    """学习路径步骤"""

    title: str = Field(..., description="步骤标题")
    knowledge_point: str = Field(..., description="知识点")
    reason: str = Field(..., description="推荐原因")


class LearningPathData(BaseModel):
    """学习路径智能体输出"""

    title: str = Field(..., description="路径标题")
    steps: list[LearningPathStepData] = Field(..., description="学习步骤")
