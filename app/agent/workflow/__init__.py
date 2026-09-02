from app.agent.knowledge import KnowledgeRetrievalAgent
from app.agent.notebook import ContentReviewAgent, NotebookChatAgent, StudioAgent
from app.agent.profile import ProfileAgent
from .chat_graph import WorkflowChatGraphMixin
from .studio_graph import WorkflowStudioGraphMixin
from .studio_tools import WorkflowStudioToolMixin
from .tool_executor import WorkflowToolExecutorMixin
from .tool_registry import WorkflowToolRegistryMixin


class NotebookAgentWorkflow(
    WorkflowChatGraphMixin,
    WorkflowToolExecutorMixin,
    WorkflowToolRegistryMixin,
    WorkflowStudioToolMixin,
    WorkflowStudioGraphMixin,
):
    """基于LangGraph编排笔记本对话和Studio多智能体协作。"""

    def __init__(
            self,
            profile_agent: ProfileAgent | None = None,
            chat_agent: NotebookChatAgent | None = None,
            studio_agent: StudioAgent | None = None,
            review_agent: ContentReviewAgent | None = None,
            knowledge_agent: KnowledgeRetrievalAgent | None = None,
            max_review_retries: int = 1,
            max_tool_iterations: int = 3,
    ):
        """
        初始化笔记本多智能体工作流
        :param profile_agent: 学生画像智能体
        :param chat_agent: 中央对话助手
        :param studio_agent: Studio产物智能体
        :param review_agent: 内容质检智能体
        :param knowledge_agent: 知识库检索智能体
        :param max_review_retries: 最大质检重试次数
        :param max_tool_iterations: 中央对话Agent最大工具执行轮数
        :return:
        """
        self.profile_agent = profile_agent or ProfileAgent()
        self.chat_agent = chat_agent or NotebookChatAgent()
        self.studio_agent = studio_agent or StudioAgent()
        self.review_agent = review_agent or ContentReviewAgent()
        self.knowledge_agent = knowledge_agent
        self.max_review_retries = max_review_retries
        self.max_tool_iterations = max_tool_iterations
        self.chat_graph = self._build_chat_graph()
        self.studio_graph = self._build_studio_graph()
