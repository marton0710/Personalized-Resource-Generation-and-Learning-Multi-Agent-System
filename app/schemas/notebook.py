# -*- coding: utf-8 -*-
"""笔记本、对话、Studio 和笔记请求 Schema。"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


ArtifactType = Literal[
    "learning_path",
    "study_guide",
    "briefing",
    "mindmap",
    "flashcards",
    "quiz",
    "data_table",
    "code_practice",
]


class NotebookCreate(BaseModel):
    """创建笔记本请求"""

    title: str = Field(..., min_length=1, max_length=256)
    description: str = Field(default="", max_length=2000)


class NotebookChat(BaseModel):
    """笔记本对话请求"""

    message: str = Field(default="", max_length=4000)
    attachment_ids: list[int] = Field(default_factory=list, max_length=4)

    @field_validator("attachment_ids")
    @classmethod
    def validate_attachment_ids(cls, value: list[int]) -> list[int]:
        """
        校验中央对话图片附件id不重复
        :param value: 图片附件id列表
        :return:
        """
        if len(value) != len(set(value)):
            raise ValueError("附件不能重复提交")
        return value


class StudioArtifactGenerate(BaseModel):
    """Studio产物生成请求"""

    artifact_type: ArtifactType
    custom_prompt: str = Field(default="", max_length=2000)
    language: str = Field(default="中文（简体）", max_length=64)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    quantity: Literal["fewer", "standard", "more"] = "standard"


class QuizAttemptSubmit(BaseModel):
    """提交测验作答结果请求"""

    answers: list[int] = Field(..., min_length=1, max_length=100)

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, value: list[int]) -> list[int]:
        """
        校验测验答案列表
        :param value: 每题选择的选项下标
        :return:
        """
        if any(answer < 0 for answer in value):
            raise ValueError("答案下标不能小于0")
        return value


class NotebookNoteCreate(BaseModel):
    """手动新建笔记请求"""

    title: str = Field(default="新笔记", min_length=1, max_length=256)
    content: str = Field(..., min_length=1, max_length=20000)


class NotebookNoteFromMessage(BaseModel):
    """将对话回复保存为笔记请求"""

    message_id: int
