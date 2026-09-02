import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.agent.workflow import NotebookAgentWorkflow
from app.schemas import ProfileAgentResult, ProfileData


class FakeProfileAgent:
    """测试用画像智能体。"""

    async def run(self, messages, current_profile=None):
        """
        返回稳定画像，避免真实模型调用
        :param messages: 对话消息
        :param current_profile: 当前画像
        :return:
        """
        return ProfileAgentResult(
            reason="测试画像",
            profile=ProfileData(learning_goal="掌握Python循环"),
        )


class FakeChatAgent:
    """模拟DeepSeek先调用Studio工具，再读取工具结果给最终回复。"""

    def __init__(self):
        """
        初始化调用计数
        :return:
        """
        self.calls = 0

    def build_agent_messages(self, notebook_title, messages, profile, source_summary=""):
        """
        构造LangChain消息上下文
        :param notebook_title: 笔记本标题
        :param messages: 最近对话
        :param profile: 学生画像
        :param source_summary: 来源通知
        :return:
        """
        return [
            SystemMessage(content="你是学习辅导智能体。"),
            HumanMessage(content=f"{notebook_title}:{messages[-1]['content']}:{source_summary}"),
        ]

    async def stream_agent_step(self, agent_messages, tools=None):
        """
        第一轮选择工具，第二轮根据ToolMessage完成回复
        :param agent_messages: LangChain消息历史
        :param tools: 可用工具
        :return:
        """
        self.calls += 1
        if self.calls == 1:
            tool_calls = [
                {
                    "name": "generate_quiz",
                    "args": {
                        "custom_prompt": "围绕Python for循环",
                        "language": "中文（简体）",
                        "difficulty": "easy",
                        "quantity": "fewer",
                    },
                    "id": "call_quiz",
                    "type": "tool_call",
                },
            ]
            yield {
                "event": "complete",
                "content": "",
                "assistant_message": AIMessage(
                    content="",
                    tool_calls=tool_calls,
                ),
            }
            return

        assert any(isinstance(message, ToolMessage) for message in agent_messages)
        yield {
            "event": "delta",
            "content": "测验已生成并完成检查。",
        }
        yield {
            "event": "complete",
            "content": "测验已生成并完成检查。请在右侧Studio查看。",
            "assistant_message": AIMessage(
                content="测验已生成并完成检查。请在右侧Studio查看。",
            ),
        }


class FakeStudioAgent:
    """测试用Studio生成智能体。"""

    async def run(self, notebook_title, messages, profile, request, review_feedback=""):
        """
        返回固定产物
        :param notebook_title: 笔记本标题
        :param messages: 最近对话
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检反馈
        :return:
        """
        assert request.artifact_type == "quiz"
        return {
            "title": "Python循环入门测验",
            "content": "# Python循环入门测验",
            "artifact_data": {
                "items": [],
            },
        }


class FakeReviewAgent:
    """测试用内容检查智能体。"""

    async def run(self, artifact_type, title, content, artifact_data, profile):
        """
        模拟检查通过
        :param artifact_type: 产物类型
        :param title: 标题
        :param content: 正文
        :param artifact_data: 结构化数据
        :param profile: 学生画像
        :return:
        """
        assert artifact_type == "quiz"
        assert title == "Python循环入门测验"
        return {
            "approved": True,
            "feedback": "检查通过",
        }


class FakeKnowledgeAgent:
    """测试用知识库检索智能体。"""

    async def search_user_sources(self, query, user_id=None, notebook_id=None, limit=5):
        """
        返回空用户资料上下文
        :param query: 检索问题
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :param limit: 用户库命中数
        :return:
        """
        return {
            "query": query,
            "hits": [],
            "context": "当前笔记本没有可检索的用户PDF资料。",
        }

    async def search_base_knowledge(self, query, limit=5):
        """
        返回固定知识库上下文
        :param query: 检索问题
        :param limit: 基础库命中数
        :return:
        """
        return {
            "query": query,
            "hits": [
                {
                    "source_scope": "base",
                    "source_label": "基础知识库",
                    "title": "Python循环",
                    "page": 1,
                    "score": 0.9,
                    "text": "for循环用于遍历序列。",
                }
            ],
            "context": "【来源1｜基础知识库｜Python循环｜页码：1】\nfor循环用于遍历序列。",
        }


class FailingStudioChatAgent:
    """模拟DeepSeek选择Studio工具后不应再被二次调用。"""

    def __init__(self):
        """
        初始化调用计数
        :return:
        """
        self.calls = 0

    def build_agent_messages(self, notebook_title, messages, profile, source_summary=""):
        """
        构造LangChain消息上下文
        :param notebook_title: 笔记本标题
        :param messages: 最近对话
        :param profile: 学生画像
        :param source_summary: 来源通知
        :return:
        """
        return [
            SystemMessage(content="你是学习辅导智能体。"),
            HumanMessage(content=f"{notebook_title}:{messages[-1]['content']}"),
        ]

    async def stream_agent_step(self, agent_messages, tools=None):
        """
        只允许第一轮选择工具
        :param agent_messages: LangChain消息历史
        :param tools: 可用工具
        :return:
        """
        self.calls += 1
        if self.calls > 1:
            raise AssertionError("Studio工具失败后不应回到模型生成正文产物")
        yield {
            "event": "complete",
            "content": "",
            "assistant_message": AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "generate_flashcards",
                        "args": {
                            "custom_prompt": "50个随机英语单词",
                            "language": "中文（简体）",
                            "difficulty": "medium",
                            "quantity": 50,
                        },
                        "id": "call_flashcards",
                        "type": "tool_call",
                    },
                ],
            ),
        }


class BrokenStudioAgent:
    """模拟Studio结构化生成失败。"""

    async def run(self, notebook_title, messages, profile, request, review_feedback=""):
        """
        抛出生成异常
        :param notebook_title: 笔记本标题
        :param messages: 最近对话
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检反馈
        :return:
        """
        raise ValueError("结构化JSON解析失败")


@pytest.mark.asyncio
async def test_deepseek_agent_calls_studio_then_reads_reviewed_tool_result():
    workflow = NotebookAgentWorkflow(
        profile_agent=FakeProfileAgent(),
        chat_agent=FakeChatAgent(),
        studio_agent=FakeStudioAgent(),
        review_agent=FakeReviewAgent(),
        knowledge_agent=FakeKnowledgeAgent(),
    )

    events = [
        event
        async for event in workflow.stream_chat(
            notebook_title="Python基础",
            messages=[
                {
                    "role": "user",
                    "content": "帮我生成一个循环测验",
                },
            ],
            current_profile=None,
        )
    ]
    final_state = events[-1]["state"]

    assert events[-1]["event"] == "complete"
    assert final_state["answer"] == "测验已生成并完成检查。请在右侧Studio查看。"
    assert final_state["tool_iterations"] == 1
    assert len(final_state["generated_artifacts"]) == 1
    assert final_state["generated_artifacts"][0]["request"].artifact_type == "quiz"
    assert any("检查" in item for item in final_state["trace"])
    assert workflow.chat_agent.calls == 2


@pytest.mark.asyncio
async def test_studio_tool_failure_blocks_chat_body_fallback():
    workflow = NotebookAgentWorkflow(
        profile_agent=FakeProfileAgent(),
        chat_agent=FailingStudioChatAgent(),
        studio_agent=BrokenStudioAgent(),
        review_agent=FakeReviewAgent(),
        knowledge_agent=FakeKnowledgeAgent(),
    )

    events = [
        event
        async for event in workflow.stream_chat(
            notebook_title="英语单词",
            messages=[
                {
                    "role": "user",
                    "content": "能不能给我50个随机英语单词，我想复习一下",
                },
            ],
            current_profile=None,
        )
    ]
    final_state = events[-1]["state"]

    assert events[-1]["event"] == "complete"
    assert final_state["blocking_error"] is True
    assert final_state["generated_artifacts"] == []
    assert "Studio 产物生成失败" in final_state["answer"]
    assert workflow.chat_agent.calls == 1
