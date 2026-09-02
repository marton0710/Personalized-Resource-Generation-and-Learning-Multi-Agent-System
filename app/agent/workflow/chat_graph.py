# -*- coding: utf-8 -*-
"""中央对话 LangGraph 节点和条件路由。"""

from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph

from .state import NotebookChatState
from app.schemas import ProfileData


class WorkflowChatGraphMixin:
    """中央对话LangGraph节点。"""

    async def stream_chat(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            current_profile: dict[str, Any] | None,
            user_id: int | None = None,
            notebook_id: int | None = None,
            source_summary: str = "",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        流式执行笔记本中央对话图
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param current_profile: 当前学生画像
        :param user_id: 当前用户id
        :param notebook_id: 当前笔记本id
        :param source_summary: 当前笔记本PDF来源概况
        :return:
        """
        latest_state: NotebookChatState = {}
        async for stream_mode, payload in self.chat_graph.astream(
                {
                    "user_id": user_id,
                    "notebook_id": notebook_id,
                    "source_summary": source_summary,
                    "notebook_title": notebook_title,
                    "messages": messages,
                    "current_profile": current_profile or {},
                    "knowledge_results": [],
                    "tool_iterations": 0,
                    "generated_artifacts": [],
                    "trace": [],
                },
                stream_mode=["custom", "values"],
        ):
            if stream_mode == "custom":
                yield payload
            else:
                latest_state = payload
        yield {
            "event": "complete",
            "state": latest_state,
        }

    def _build_chat_graph(self):
        """
        构建中央对话LangGraph状态图
        :return:
        """
        graph = StateGraph(NotebookChatState)
        graph.add_node("profile_analysis", self._profile_analysis)
        graph.add_node("tutor_agent", self._tutor_agent)
        graph.add_node("tool_executor", self._execute_tools)
        graph.add_node("tool_limit", self._tool_limit_response)
        graph.add_edge(START, "profile_analysis")
        graph.add_edge("profile_analysis", "tutor_agent")
        graph.add_conditional_edges(
            "tutor_agent",
            self._select_chat_route,
            {
                "tools": "tool_executor",
                "limit": "tool_limit",
                "finished": END,
            },
        )
        graph.add_conditional_edges(
            "tool_executor",
            self._select_after_tool_execution,
            {
                "continue": "tutor_agent",
                "finished": END,
            },
        )
        graph.add_edge("tool_limit", END)
        return graph.compile()

    async def _profile_analysis(self, state: NotebookChatState) -> NotebookChatState:
        """
        执行画像分析节点
        :param state: 中央对话状态
        :return:
        """
        writer = get_stream_writer()
        writer({
            "event": "status",
            "message": "画像智能体正在分析学习需求",
        })
        result = await self.profile_agent.run(
            messages=state["messages"],
            current_profile=state["current_profile"],
        )
        return {
            "profile_result": result,
            "agent_messages": self._build_agent_messages(
                notebook_title=state["notebook_title"],
                messages=state["messages"],
                profile=result.profile,
                source_summary=state.get("source_summary", ""),
            ),
            "trace": [
                *state["trace"],
                "画像智能体：分析对话并更新七维动态学习画像",
            ],
        }

    async def _tutor_agent(self, state: NotebookChatState) -> NotebookChatState:
        """
        执行一轮学习辅导Agent推理
        :param state: 中央对话状态
        :return:
        """
        writer = get_stream_writer()
        tool_iterations = state.get("tool_iterations", 0)
        writer({
            "event": "status",
            "message": (
                "学习辅导智能体正在读取工具结果并决定下一步"
                if tool_iterations
                else "学习辅导智能体正在自主判断是否需要调用工具"
            ),
        })
        assistant_message = AIMessage(content="")
        delta_events = []
        runtime_tool_map = self._build_runtime_tool_map(state)
        async for event in self.chat_agent.stream_agent_step(
            agent_messages=state["agent_messages"],
            tools=list(runtime_tool_map.values()),
        ):
            if event["event"] == "delta":
                delta_events.append(event)
            else:
                assistant_message = event["assistant_message"]
        if assistant_message.tool_calls:
            trace_message = f"学习辅导智能体：第{tool_iterations + 1}轮自主选择{len(assistant_message.tool_calls)}个工具"
        else:
            for event in delta_events:
                writer(event)
            trace_message = "学习辅导智能体：无需继续调用工具，生成最终辅导回复"
        answer = self._message_content_to_text(assistant_message.content)
        if not assistant_message.tool_calls and not answer.strip():
            answer = "我已经完成本轮处理，但没有生成有效回复。请换个问法或补充更明确的学习目标。"
            writer({"event": "delta", "content": answer})
        return {
            "answer": answer,
            "agent_messages": [*state["agent_messages"], assistant_message],
            "trace": [*state["trace"], trace_message],
        }

    def _select_chat_route(self, state: NotebookChatState) -> str:
        """
        选择中央对话后续路由
        :param state: 中央对话状态
        :return:
        """
        last_ai_message = self._last_ai_message(state)
        if last_ai_message is None or not last_ai_message.tool_calls:
            return "finished"
        if state.get("tool_iterations", 0) >= self.max_tool_iterations:
            return "limit"
        return "tools"

    @staticmethod
    def _select_after_tool_execution(state: NotebookChatState) -> str:
        """
        选择工具执行后的后续路由
        :param state: 中央对话状态
        :return:
        """
        if state.get("blocking_error"):
            return "finished"
        return "continue"

    def _build_agent_messages(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            source_summary: str,
    ) -> list[BaseMessage]:
        """
        构建真实对话智能体消息
        :param notebook_title: 笔记本标题
        :param messages: 最近对话
        :param profile: 学生画像
        :param source_summary: 当前笔记本PDF来源概况
        :return:
        """
        return self.chat_agent.build_agent_messages(
            notebook_title=notebook_title,
            messages=messages,
            profile=profile,
            source_summary=source_summary,
        )

    @staticmethod
    def _last_ai_message(state: NotebookChatState) -> AIMessage | None:
        """
        获取最近一条AIMessage
        :param state: 中央对话状态
        :return:
        """
        for message in reversed(state.get("agent_messages", [])):
            if isinstance(message, AIMessage):
                return message
        return None

    @staticmethod
    def _message_content_to_text(content: str | list[Any]) -> str:
        """
        将LangChain消息内容规整为文本
        :param content: 消息内容
        :return:
        """
        if isinstance(content, str):
            return content
        return "".join(
            item.get("text", "")
            if isinstance(item, dict) and item.get("type") == "text"
            else str(item)
            for item in content
        )
