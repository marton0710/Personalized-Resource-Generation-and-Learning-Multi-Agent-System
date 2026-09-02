# -*- coding: utf-8 -*-
"""中央对话每轮可调用工具注册逻辑。"""

from typing import Any

from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer

from app.agent.knowledge import (
    BaseKnowledgeSearchTool,
    KnowledgeRetrievalAgent,
    UserKnowledgeSearchTool,
)
from app.agent.notebook import STUDIO_TOOL_ARTIFACT_TYPES, build_studio_langchain_tool
from .state import NotebookChatState


class WorkflowToolRegistryMixin:
    """运行时工具注册表。"""

    def _build_runtime_tool_map(self, state: NotebookChatState) -> dict[str, BaseTool]:
        """
        构造本轮DeepSeek可自主调用的LangChain工具映射
        :param state: 中央对话状态
        :return:
        """
        return {
            **self._build_runtime_knowledge_tools(state),
            **self._build_runtime_studio_tools(state),
        }

    def _build_runtime_knowledge_tools(self, state: NotebookChatState) -> dict[str, BaseTool]:
        """
        构造带当前笔记本上下文的知识库检索工具集合
        :param state: 中央对话状态
        :return:
        """
        knowledge_agent = self.knowledge_agent or KnowledgeRetrievalAgent()
        tools = [
            UserKnowledgeSearchTool(
                knowledge_agent=knowledge_agent,
                user_id=state.get("user_id"),
                notebook_id=state.get("notebook_id"),
                status_writer=self._write_stream_event,
            ),
            BaseKnowledgeSearchTool(
                knowledge_agent=knowledge_agent,
                status_writer=self._write_stream_event,
            ),
        ]
        return {
            tool.name: tool.as_langchain_tool()
            for tool in tools
        }

    def _build_runtime_studio_tools(self, state: NotebookChatState) -> dict[str, BaseTool]:
        """
        构造带当前LangGraph状态闭包的Studio工具集合
        :param state: 中央对话状态
        :return:
        """
        return {
            tool_name: build_studio_langchain_tool(
                tool_name=tool_name,
                coroutine=self._make_runtime_studio_tool(
                    state=state,
                    tool_name=tool_name,
                    artifact_type=artifact_type,
                ),
                response_format="content_and_artifact",
            )
            for tool_name, artifact_type in STUDIO_TOOL_ARTIFACT_TYPES.items()
        }

    @staticmethod
    def _write_stream_event(event: dict[str, Any]) -> None:
        """
        写入LangGraph自定义流事件
        :param event: 流事件
        :return:
        """
        get_stream_writer()(event)
