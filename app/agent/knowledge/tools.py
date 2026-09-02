# -*- coding: utf-8 -*-
"""知识库检索工具类。"""

import json
from collections.abc import Callable
from typing import Any

from langchain_core.tools import StructuredTool

from .retrieval import KnowledgeRetrievalAgent
from .types import KnowledgeSearchArgs


StatusWriter = Callable[[dict[str, Any]], None]


class UserKnowledgeSearchTool:
    """当前笔记本用户PDF资料检索工具。"""

    name = "search_user_sources"
    description = (
        "检索当前笔记本中用户上传的PDF资料库。"
        "当用户要求依据上传资料、PDF来源、当前笔记本材料或需要优先查个人资料时调用。"
    )
    args_schema = KnowledgeSearchArgs

    def __init__(
            self,
            knowledge_agent: KnowledgeRetrievalAgent,
            user_id: int | None = None,
            notebook_id: int | None = None,
            status_writer: StatusWriter | None = None,
    ):
        """
        初始化用户PDF资料检索工具
        :param knowledge_agent: 知识库检索智能体
        :param user_id: 当前用户id
        :param notebook_id: 当前笔记本id
        :param status_writer: 可选运行状态回调
        :return:
        """
        self.knowledge_agent = knowledge_agent
        self.user_id = user_id
        self.notebook_id = notebook_id
        self.status_writer = status_writer

    async def search(self, query: str) -> dict[str, Any]:
        """
        检索当前笔记本用户PDF资料
        :param query: 检索问题
        :return:
        """
        return await self.knowledge_agent.search_user_sources(
            query=query or "当前笔记本主题",
            user_id=self.user_id,
            notebook_id=self.notebook_id,
        )

    async def run(self, query: str) -> tuple[str, dict[str, Any]]:
        """
        执行Agent工具调用
        :param query: 检索问题
        :return:
        """
        if self.status_writer:
            self.status_writer({
                "event": "status",
                "message": "学习辅导智能体正在检索用户PDF资料",
            })
        result = await self.search(query=query)
        return _format_knowledge_tool_response(
            query=query or "当前笔记本主题",
            result=result,
            source_scope="user_pdf",
            source_label="用户PDF",
            trace_label="用户资料检索智能体",
        )

    def as_langchain_tool(self) -> StructuredTool:
        """
        转换为LangChain工具
        :return:
        """
        return StructuredTool.from_function(
            coroutine=self.run,
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
            response_format="content_and_artifact",
        )


class BaseKnowledgeSearchTool:
    """系统基础知识库检索工具。"""

    name = "search_base_knowledge"
    description = (
        "检索系统基础知识库。"
        "当用户PDF资料不足、没有命中，或需要补充通用课程知识、概念解释、例题背景时调用。"
    )
    args_schema = KnowledgeSearchArgs

    def __init__(
            self,
            knowledge_agent: KnowledgeRetrievalAgent,
            status_writer: StatusWriter | None = None,
    ):
        """
        初始化基础知识库检索工具
        :param knowledge_agent: 知识库检索智能体
        :param status_writer: 可选运行状态回调
        :return:
        """
        self.knowledge_agent = knowledge_agent
        self.status_writer = status_writer

    async def search(self, query: str) -> dict[str, Any]:
        """
        检索系统基础知识库
        :param query: 检索问题
        :return:
        """
        return await self.knowledge_agent.search_base_knowledge(
            query=query or "当前笔记本主题",
        )

    async def run(self, query: str) -> tuple[str, dict[str, Any]]:
        """
        执行Agent工具调用
        :param query: 检索问题
        :return:
        """
        if self.status_writer:
            self.status_writer({
                "event": "status",
                "message": "学习辅导智能体正在检索基础知识库",
            })
        result = await self.search(query=query)
        return _format_knowledge_tool_response(
            query=query or "当前笔记本主题",
            result=result,
            source_scope="base",
            source_label="基础知识库",
            trace_label="基础库检索智能体",
        )

    def as_langchain_tool(self) -> StructuredTool:
        """
        转换为LangChain工具
        :return:
        """
        return StructuredTool.from_function(
            coroutine=self.run,
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
            response_format="content_and_artifact",
        )


def _format_knowledge_tool_response(
        query: str,
        result: dict[str, Any],
        source_scope: str,
        source_label: str,
        trace_label: str,
) -> tuple[str, dict[str, Any]]:
    """
    格式化知识库工具返回值
    :param query: 检索问题
    :param result: 检索结果
    :param source_scope: 来源范围
    :param source_label: 来源标签
    :param trace_label: 轨迹标签
    :return:
    """
    hit_count = len(result.get("hits", []))
    content = json.dumps(
        {
            "status": "ok",
            "source": source_scope,
            "query": query,
            "hits": hit_count,
            "context": result.get("context", ""),
        },
        ensure_ascii=False,
    )
    artifact = {
        "knowledge_result": result,
        "trace": [f"{trace_label}：命中{source_label} {hit_count} 条"],
    }
    return content, artifact
