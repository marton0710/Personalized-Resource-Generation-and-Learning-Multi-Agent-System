# -*- coding: utf-8 -*-
"""Studio 生成 LangGraph 子图和质检重试节点。"""

from langgraph.graph import END, START, StateGraph

from app.agent.notebook import STUDIO_SPECS
from .state import StudioState
from app.schemas import ProfileData
from app.schemas.notebook import StudioArtifactGenerate


class WorkflowStudioGraphMixin:
    """Studio生成LangGraph节点。"""

    async def run_studio(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            request: StudioArtifactGenerate,
    ) -> StudioState:
        """
        执行Studio学习产物生成图
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param profile: 学生画像
        :param request: Studio生成请求
        :return:
        """
        return await self.studio_graph.ainvoke({
            "notebook_title": notebook_title,
            "messages": messages,
            "profile": profile,
            "request": request,
            "review_attempts": 0,
            "review_feedback": "",
            "trace": [],
        })

    def _build_studio_graph(self):
        """
        构建Studio生成LangGraph状态图
        :return:
        """
        graph = StateGraph(StudioState)
        graph.add_node("supervisor", self._supervisor)
        for artifact_type in STUDIO_SPECS:
            graph.add_node(artifact_type, self._generate_artifact)
            graph.add_edge(artifact_type, "quality_review")
        graph.add_node("quality_review", self._quality_review)
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges(
            "supervisor",
            self._select_worker,
            {
                artifact_type: artifact_type
                for artifact_type in STUDIO_SPECS
            },
        )
        graph.add_conditional_edges(
            "quality_review",
            self._review_decision,
            {
                "approved": END,
                "retry": "supervisor",
                "finished": END,
            },
        )
        return graph.compile()

    async def _supervisor(self, state: StudioState) -> StudioState:
        """
        调度Studio专门智能体
        :param state: Studio工作流状态
        :return:
        """
        artifact_type = state["request"].artifact_type
        worker_name = STUDIO_SPECS[artifact_type].role
        retry_suffix = "，携带质检反馈重新生成" if state.get("review_feedback") else ""
        return {
            "route": artifact_type,
            "trace": [
                *state["trace"],
                f"Supervisor调度节点：分派给{worker_name}{retry_suffix}",
            ],
        }

    @staticmethod
    def _select_worker(state: StudioState) -> str:
        """
        选择Studio专门智能体路由
        :param state: Studio工作流状态
        :return:
        """
        return state["route"]

    async def _generate_artifact(self, state: StudioState) -> StudioState:
        """
        执行Studio学习产物生成节点
        :param state: Studio工作流状态
        :return:
        """
        artifact = await self.studio_agent.run(
            notebook_title=state["notebook_title"],
            messages=state["messages"],
            profile=state["profile"],
            request=state["request"],
            review_feedback=state.get("review_feedback", ""),
        )
        worker_name = STUDIO_SPECS[state["route"]].role
        return {
            "artifact": artifact,
            "trace": [
                *state["trace"],
                f"{worker_name}：完成个性化学习产物生成",
            ],
        }

    async def _quality_review(self, state: StudioState) -> StudioState:
        """
        执行Studio学习产物质检节点
        :param state: Studio工作流状态
        :return:
        """
        artifact = state["artifact"]
        review = await self.review_agent.run(
            artifact_type=state["route"],
            title=artifact["title"],
            content=artifact["content"],
            artifact_data=artifact["artifact_data"],
            profile=state["profile"],
        )
        attempts = state.get("review_attempts", 0) + 1
        if review["approved"]:
            trace_message = "内容质检智能体：检查通过，可以发布"
        elif attempts <= self.max_review_retries:
            trace_message = f"内容质检智能体：检查未通过，反馈为“{review['feedback']}”"
        else:
            trace_message = "内容质检智能体：已达到自动重试上限，保留最后一次生成结果"
        return {
            "approved": review["approved"],
            "review_feedback": review["feedback"],
            "review_attempts": attempts,
            "trace": [*state["trace"], trace_message],
        }

    def _review_decision(self, state: StudioState) -> str:
        """
        根据质检结果选择后续路由
        :param state: Studio工作流状态
        :return:
        """
        if state["approved"]:
            return "approved"
        if state["review_attempts"] <= self.max_review_retries:
            return "retry"
        return "finished"
