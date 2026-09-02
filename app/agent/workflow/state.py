# -*- coding: utf-8 -*-
"""笔记本对话和 Studio 生成的 LangGraph 状态定义。"""

from typing import Any, TypedDict

from langchain_core.messages import BaseMessage, ToolMessage

from app.schemas import ProfileAgentResult, ProfileData
from app.schemas.notebook import StudioArtifactGenerate


class NotebookChatState(TypedDict, total=False):
    """中央对话LangGraph状态。"""

    user_id: int | None
    notebook_id: int | None
    source_summary: str
    notebook_title: str
    messages: list[dict[str, str]]
    current_profile: dict[str, Any]
    profile_result: ProfileAgentResult
    knowledge_results: list[dict[str, Any]]
    agent_messages: list[BaseMessage | dict[str, Any]]
    answer: str
    tool_messages: list[ToolMessage]
    tool_iterations: int
    generated_artifacts: list[dict[str, Any]]
    blocking_error: bool
    trace: list[str]


class StudioState(TypedDict, total=False):
    """Studio生成LangGraph状态。"""

    notebook_title: str
    messages: list[dict[str, str]]
    profile: ProfileData
    request: StudioArtifactGenerate
    route: str
    artifact: dict[str, Any]
    review_feedback: str
    review_attempts: int
    approved: bool
    trace: list[str]
