# -*- coding: utf-8 -*-
"""中央对话运行时 Studio 工具协程。"""

import json
import re
from typing import Any

from langchain_core.messages import ToolMessage
from langgraph.config import get_stream_writer

from app.agent.notebook import STUDIO_SPECS
from .state import NotebookChatState
from app.schemas.notebook import StudioArtifactGenerate


QUANTITY_LABELS = {"fewer", "standard", "more"}
QUANTITY_ALIASES = {
    "少量": "fewer",
    "较少": "fewer",
    "标准": "standard",
    "适中": "standard",
    "更多": "more",
    "大量": "more",
}


class WorkflowStudioToolMixin:
    """Studio生成运行时工具。"""

    def _messages_with_knowledge_results(self, state: NotebookChatState) -> list[dict[str, str]]:
        """
        为Studio子图补充已经通过工具检索到的知识库上下文
        :param state: 中央对话状态
        :return:
        """
        knowledge_context = self._format_knowledge_results_context(
            knowledge_results=state.get("knowledge_results", []),
        )
        if not knowledge_context:
            return state["messages"]
        return [
            *state["messages"],
            {
                "role": "assistant",
                "content": f"[知识库工具检索结果]\n{knowledge_context}",
            },
        ]

    @staticmethod
    def _format_knowledge_results_context(
            knowledge_results: list[dict[str, Any]],
            max_chars: int = 5200,
    ) -> str:
        """
        汇总工具检索结果，控制传给Studio子图的上下文长度
        :param knowledge_results: 已执行的知识库检索结果
        :param max_chars: 最大字符数
        :return:
        """
        sections = []
        used = 0
        for result in knowledge_results:
            query = result.get("query") or "未命名检索"
            context = str(result.get("context") or "").strip()
            if not context:
                continue
            section = f"检索问题：{query}\n{context}"
            if used + len(section) > max_chars:
                break
            sections.append(section)
            used += len(section)
        return "\n\n".join(sections)

    def _make_runtime_studio_tool(
            self,
            state: NotebookChatState,
            tool_name: str,
            artifact_type: str,
    ):
        """
        为单个Studio工具创建运行时协程
        :param state: 中央对话状态
        :param tool_name: 工具名称
        :param artifact_type: Studio产物类型
        :return:
        """
        async def run_studio_tool(
                custom_prompt: str = "",
                language: str = "中文（简体）",
                difficulty: str = "medium",
                quantity: int | str | None = "standard",
        ) -> tuple[str, dict[str, Any]]:
            """
            执行Studio生成和检查子图
            :param custom_prompt: 用户补充要求
            :param language: 输出语言
            :param difficulty: 难度
            :param quantity: 数量
            :return:
            """
            writer = get_stream_writer()
            quantity_label, explicit_count = self._normalize_quantity_arg(quantity)
            prompt = self._merge_explicit_count_into_prompt(
                custom_prompt=custom_prompt,
                explicit_count=explicit_count,
            )
            request = StudioArtifactGenerate.model_validate({
                "artifact_type": artifact_type,
                "custom_prompt": prompt,
                "language": language,
                "difficulty": difficulty,
                "quantity": quantity_label,
            })
            label = STUDIO_SPECS[artifact_type].label
            writer({
                "event": "tool_start",
                "artifact_type": artifact_type,
                "message": f"DeepSeek已选择{label}Studio，正在生成内容并调用检查智能体",
            })
            studio_state = await self.run_studio(
                notebook_title=state["notebook_title"],
                messages=self._messages_with_knowledge_results(state),
                profile=state["profile_result"].profile,
                request=request,
            )
            writer({"event": "tool_end", "artifact_type": artifact_type})
            trace = [
                *studio_state["trace"],
                f"Studio工具执行器：{label}生成和检查结果已回传给DeepSeek学习辅导智能体",
            ]
            content = json.dumps(
                {
                    "status": "generated",
                    "artifact_type": artifact_type,
                    "title": studio_state["artifact"]["title"],
                    "quality_approved": studio_state["approved"],
                    "review_feedback": studio_state.get("review_feedback", ""),
                    "message": "内容已由Studio生成并完成检查流程，随后会保存到右侧Studio的已生成内容区域。",
                },
                ensure_ascii=False,
            )
            artifact = {
                "generated": {
                    "request": request,
                    "workflow_state": studio_state,
                },
                "trace": trace,
                "tool_name": tool_name,
            }
            return content, artifact

        return run_studio_tool

    @staticmethod
    def _tool_error_message(tool_call_id: str, tool_name: str, message: str) -> ToolMessage:
        """
        组装工具错误消息
        :param tool_call_id: 工具调用id
        :param tool_name: 工具名称
        :param message: 错误说明
        :return:
        """
        return ToolMessage(
            tool_call_id=tool_call_id,
            name=tool_name,
            content=json.dumps({
                "status": "error",
                "message": message,
            }, ensure_ascii=False),
        )

    @staticmethod
    def _normalize_quantity_arg(quantity: int | str | None) -> tuple[str, int | None]:
        """
        将模型给出的数量参数归一化为后端三档，并保留明确数量
        :param quantity: 工具调用原始数量参数
        :return:
        """
        if isinstance(quantity, bool) or quantity is None:
            return "standard", None
        if isinstance(quantity, int):
            return WorkflowStudioToolMixin._quantity_label_from_count(quantity), quantity
        value = quantity.strip()
        if value in QUANTITY_LABELS:
            return value, None
        if value in QUANTITY_ALIASES:
            return QUANTITY_ALIASES[value], None
        match = re.search(r"\d{1,3}", value)
        if match:
            count = int(match.group())
            return WorkflowStudioToolMixin._quantity_label_from_count(count), count
        return "standard", None

    @staticmethod
    def _quantity_label_from_count(count: int) -> str:
        """
        将明确数量映射到现有API三档，保留手动Studio入口兼容性
        :param count: 明确数量
        :return:
        """
        if count <= 5:
            return "fewer"
        if count <= 12:
            return "standard"
        return "more"

    @staticmethod
    def _merge_explicit_count_into_prompt(custom_prompt: str, explicit_count: int | None) -> str:
        """
        将工具数量参数中的明确数量并入生成提示词
        :param custom_prompt: 用户补充要求
        :param explicit_count: 明确数量
        :return:
        """
        prompt = custom_prompt.strip()
        if explicit_count is None:
            return prompt
        count_note = f"明确数量：{explicit_count}个"
        if str(explicit_count) in prompt:
            return prompt
        return f"{prompt}\n{count_note}" if prompt else count_note
