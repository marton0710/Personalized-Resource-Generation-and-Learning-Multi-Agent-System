# -*- coding: utf-8 -*-
"""中央对话 LangGraph 工具调用执行节点。"""

from langgraph.config import get_stream_writer

from app.agent.notebook import STUDIO_TOOL_ARTIFACT_TYPES
from .state import NotebookChatState


class WorkflowToolExecutorMixin:
    """中央对话工具调用执行节点。"""

    async def _execute_tools(self, state: NotebookChatState) -> NotebookChatState:
        """
        执行中央对话自主选择的工具
        :param state: 中央对话状态
        :return:
        """
        generated_artifacts = list(state.get("generated_artifacts", []))
        knowledge_results = list(state.get("knowledge_results", []))
        tool_messages = []
        studio_failures = []
        trace = list(state["trace"])
        next_iteration = state.get("tool_iterations", 0) + 1
        last_ai_message = self._last_ai_message(state)
        for tool_call in last_ai_message.tool_calls if last_ai_message else []:
            tool_name = tool_call["name"]
            runtime_tools = self._build_runtime_tool_map({
                **state,
                "knowledge_results": knowledge_results,
            })
            tool = runtime_tools.get(tool_name)
            if tool is None:
                tool_messages.append(self._tool_error_message(
                    tool_call_id=tool_call["id"],
                    tool_name=tool_name,
                    message=f"未知工具：{tool_name}",
                ))
                trace.append(f"工具执行器：拒绝未知工具 {tool_name}")
                continue
            try:
                tool_message = await tool.ainvoke(tool_call)
            except Exception as e:
                error_message = str(e)
                tool_messages.append(self._tool_error_message(
                    tool_call_id=tool_call["id"],
                    tool_name=tool_name,
                    message=f"工具执行失败：{error_message}",
                ))
                trace.append(f"工具执行器：{tool_name} 执行失败：{error_message}")
                if tool_name in STUDIO_TOOL_ARTIFACT_TYPES:
                    studio_failures.append(f"{tool_name}：{error_message}")
                continue

            tool_messages.append(tool_message)
            artifact = tool_message.artifact or {}
            if artifact.get("generated"):
                generated_artifacts.append(artifact["generated"])
            if artifact.get("knowledge_result"):
                knowledge_results.append(artifact["knowledge_result"])
            trace.extend(artifact.get("trace", []))
        result = {
            "agent_messages": [*state["agent_messages"], *tool_messages],
            "knowledge_results": knowledge_results,
            "generated_artifacts": generated_artifacts,
            "tool_messages": tool_messages,
            "tool_iterations": next_iteration,
            "trace": trace,
        }
        if studio_failures:
            answer = (
                "Studio 产物生成失败，已停止本轮自动补写，避免在聊天正文中生成未保存的完整产物。"
                f"失败原因：{studio_failures[0]}。请稍后重试，或先把数量/范围缩小后再生成。"
            )
            get_stream_writer()({"event": "delta", "content": answer})
            return {
                **result,
                "answer": answer,
                "blocking_error": True,
                "trace": [
                    *trace,
                    "工具执行器：Studio工具失败，阻止学习辅导智能体绕过Studio生成正文产物",
                ],
            }
        return result

    async def _tool_limit_response(self, state: NotebookChatState) -> NotebookChatState:
        """
        工具循环达到上限时给出受控回复
        :param state: 中央对话状态
        :return:
        """
        writer = get_stream_writer()
        answer = (
            "本轮工具调用已经达到上限。我已停止继续调用工具，"
            "请根据右侧已生成内容查看已有结果；如果还需要更多产物，可以再发起一次更明确的请求。"
        )
        writer({"event": "delta", "content": answer})
        return {
            "answer": answer,
            "trace": [
                *state["trace"],
                "学习辅导智能体：工具循环达到上限，停止继续调用工具",
            ],
        }
