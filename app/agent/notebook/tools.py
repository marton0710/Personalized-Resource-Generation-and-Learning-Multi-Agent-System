# -*- coding: utf-8 -*-
"""Studio 产物工具类和 DeepSeek 可调用工具声明。"""

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from app.agent.client import DeepSeekClient
from app.agent.path import LearningPathAgent
from .specs import STUDIO_SPECS, STUDIO_TOOL_ARTIFACT_TYPES
from app.schemas import ProfileData
from app.schemas.notebook import StudioArtifactGenerate


QUIZ_COUNTS = {"fewer": 4, "standard": 6, "more": 8}
FLASHCARD_COUNTS = {"fewer": 6, "standard": 10, "more": 14}
QUIZ_BATCH_SIZE = 8
FLASHCARD_BATCH_SIZE = 12
EXPLICIT_COUNT_PATTERN = re.compile(
    r"(?:明确数量|数量|生成|给我|整理|做成)?[^\d]{0,12}(\d{1,3})\s*"
    r"(?:个|张|道|题|条|组|项|份|cards?|flashcards?|questions?|words?|单词|词汇|术语|概念)",
    re.IGNORECASE,
)


class StudioToolArgs(BaseModel):
    """LangChain工具入参：由学习辅导Agent自主填充。"""

    custom_prompt: str = Field(
        default="",
        description="用户的原始目标和补充要求，包括主题、范围、明确数量、难度偏好、输出形态或使用场景；没有时传空字符串。",
    )
    language: Literal["中文（简体）", "English"] = Field(
        default="中文（简体）",
        description="产物语言。",
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(
        default="medium",
        description="适用于测验、闪卡和练习类产物的难度，其他工具可以使用默认值medium。",
    )
    quantity: int | str | None = Field(
        default="standard",
        description="测验和闪卡的数量要求。可以传fewer/standard/more，也可以直接传用户指定的整数数量；没有明确数量时传standard或省略。",
    )


class LearningPathStudioTool:
    """学习路径Studio工具。"""

    artifact_type = "learning_path"

    def __init__(self, client: DeepSeekClient):
        """
        初始化学习路径Studio工具
        :param client: DeepSeek客户端
        :return:
        """
        self.path_agent = LearningPathAgent(client=client)

    async def run(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            request: StudioArtifactGenerate,
            review_feedback: str = "",
    ) -> dict[str, Any]:
        """
        生成个性化学习路径
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检改进意见
        :return:
        """
        topic = notebook_title
        if request.custom_prompt:
            topic = f"{notebook_title}。补充要求：{request.custom_prompt}"
        if review_feedback:
            topic = f"{topic}。质检改进意见：{review_feedback}"
        path = await self.path_agent.run(
            profile=profile,
            course_topic=topic,
        )
        rows = [
            f"{index}. **{step.title}**：{step.knowledge_point}\n   - 推荐原因：{step.reason}"
            for index, step in enumerate(path.steps, start=1)
        ]
        return {
            "title": path.title,
            "content": f"# {path.title}\n\n" + "\n".join(rows),
            "artifact_data": path.model_dump(mode="json"),
        }


class StudyGuideStudioTool:
    """学习指南Studio工具。"""

    artifact_type = "study_guide"

    def __init__(self, client: DeepSeekClient):
        """
        初始化学习指南Studio工具
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client

    async def run(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            request: StudioArtifactGenerate,
            review_feedback: str = "",
    ) -> dict[str, Any]:
        """
        生成学习指南
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检改进意见
        :return:
        """
        return await _generate_markdown_studio_artifact(
            client=self.client,
            artifact_type=self.artifact_type,
            notebook_title=notebook_title,
            messages=messages,
            profile=profile,
            request=request,
            review_feedback=review_feedback,
        )


class BriefingStudioTool:
    """拓展报告Studio工具。"""

    artifact_type = "briefing"

    def __init__(self, client: DeepSeekClient):
        """
        初始化拓展报告Studio工具
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client

    async def run(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            request: StudioArtifactGenerate,
            review_feedback: str = "",
    ) -> dict[str, Any]:
        """
        生成拓展报告
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检改进意见
        :return:
        """
        return await _generate_markdown_studio_artifact(
            client=self.client,
            artifact_type=self.artifact_type,
            notebook_title=notebook_title,
            messages=messages,
            profile=profile,
            request=request,
            review_feedback=review_feedback,
        )


class MindmapStudioTool:
    """思维导图Studio工具。"""

    artifact_type = "mindmap"

    def __init__(self, client: DeepSeekClient):
        """
        初始化思维导图Studio工具
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client

    async def run(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            request: StudioArtifactGenerate,
            review_feedback: str = "",
    ) -> dict[str, Any]:
        """
        生成思维导图
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检改进意见
        :return:
        """
        return await _generate_markdown_studio_artifact(
            client=self.client,
            artifact_type=self.artifact_type,
            notebook_title=notebook_title,
            messages=messages,
            profile=profile,
            request=request,
            review_feedback=review_feedback,
        )


class DataTableStudioTool:
    """数据表格Studio工具。"""

    artifact_type = "data_table"

    def __init__(self, client: DeepSeekClient):
        """
        初始化数据表格Studio工具
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client

    async def run(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            request: StudioArtifactGenerate,
            review_feedback: str = "",
    ) -> dict[str, Any]:
        """
        生成数据表格
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检改进意见
        :return:
        """
        return await _generate_markdown_studio_artifact(
            client=self.client,
            artifact_type=self.artifact_type,
            notebook_title=notebook_title,
            messages=messages,
            profile=profile,
            request=request,
            review_feedback=review_feedback,
        )


class CodePracticeStudioTool:
    """代码实操Studio工具。"""

    artifact_type = "code_practice"

    def __init__(self, client: DeepSeekClient):
        """
        初始化代码实操Studio工具
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client

    async def run(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            request: StudioArtifactGenerate,
            review_feedback: str = "",
    ) -> dict[str, Any]:
        """
        生成代码实操
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检改进意见
        :return:
        """
        return await _generate_markdown_studio_artifact(
            client=self.client,
            artifact_type=self.artifact_type,
            notebook_title=notebook_title,
            messages=messages,
            profile=profile,
            request=request,
            review_feedback=review_feedback,
        )


class QuizStudioTool:
    """测验Studio工具。"""

    artifact_type = "quiz"

    def __init__(self, client: DeepSeekClient):
        """
        初始化测验Studio工具
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client

    async def run(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            request: StudioArtifactGenerate,
            review_feedback: str = "",
    ) -> dict[str, Any]:
        """
        生成结构化单项选择题
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检改进意见
        :return:
        """
        count = _resolve_item_count(
            request=request,
            default_counts=QUIZ_COUNTS,
            max_count=30,
        )
        items = await _generate_quiz_items(
            client=self.client,
            notebook_title=notebook_title,
            messages=messages,
            profile=profile,
            request=request,
            review_feedback=review_feedback,
            count=count,
        )
        return {
            "title": f"{notebook_title} · 测验",
            "content": f"# {notebook_title} · 测验\n\n共 {len(items)} 道单项选择题。",
            "artifact_data": {"items": items},
        }


class FlashcardStudioTool:
    """闪卡Studio工具。"""

    artifact_type = "flashcards"

    def __init__(self, client: DeepSeekClient):
        """
        初始化闪卡Studio工具
        :param client: DeepSeek客户端
        :return:
        """
        self.client = client

    async def run(
            self,
            notebook_title: str,
            messages: list[dict[str, str]],
            profile: ProfileData,
            request: StudioArtifactGenerate,
            review_feedback: str = "",
    ) -> dict[str, Any]:
        """
        生成结构化复习闪卡
        :param notebook_title: 笔记本标题
        :param messages: 最近对话消息
        :param profile: 学生画像
        :param request: Studio生成请求
        :param review_feedback: 质检改进意见
        :return:
        """
        count = _resolve_item_count(
            request=request,
            default_counts=FLASHCARD_COUNTS,
            max_count=80,
        )
        items = await _generate_flashcard_items(
            client=self.client,
            notebook_title=notebook_title,
            messages=messages,
            profile=profile,
            request=request,
            review_feedback=review_feedback,
            count=count,
        )
        return {
            "title": f"{notebook_title} · 闪卡",
            "content": f"# {notebook_title} · 闪卡\n\n共 {len(items)} 张复习闪卡。",
            "artifact_data": {"items": items},
        }


STUDIO_TOOL_CLASSES = {
    "learning_path": LearningPathStudioTool,
    "study_guide": StudyGuideStudioTool,
    "briefing": BriefingStudioTool,
    "mindmap": MindmapStudioTool,
    "flashcards": FlashcardStudioTool,
    "quiz": QuizStudioTool,
    "data_table": DataTableStudioTool,
    "code_practice": CodePracticeStudioTool,
}


def build_studio_tools(client: DeepSeekClient) -> dict[str, Any]:
    """
    创建Studio产物工具注册表
    :param client: DeepSeek客户端
    :return:
    """
    missing_types = set(STUDIO_SPECS) - set(STUDIO_TOOL_CLASSES)
    if missing_types:
        names = "、".join(sorted(missing_types))
        raise RuntimeError(f"Studio工具缺失：{names}")
    return {
        artifact_type: tool_class(client=client)
        for artifact_type, tool_class in STUDIO_TOOL_CLASSES.items()
    }


def build_studio_langchain_tool(
        tool_name: str,
        coroutine: Callable[..., Awaitable[Any]],
        response_format: Literal["content", "content_and_artifact"] = "content",
) -> StructuredTool:
    """
    构造DeepSeek可自主调用的Studio工具声明
    :param tool_name: 工具名称
    :param coroutine: 工具协程函数
    :param response_format: LangChain工具返回格式
    :return:
    """
    artifact_type = STUDIO_TOOL_ARTIFACT_TYPES[tool_name]
    spec = STUDIO_SPECS[artifact_type]
    return StructuredTool.from_function(
        coroutine=coroutine,
        name=tool_name,
        description=(
            f"调用{spec.role}，"
            f"生成可保存到右侧Studio的{spec.label}。"
            f"{spec.requirement}"
        ),
        args_schema=StudioToolArgs,
        response_format=response_format,
    )


async def _generate_quiz_items(
        client: DeepSeekClient,
        notebook_title: str,
        messages: list[dict[str, str]],
        profile: ProfileData,
        request: StudioArtifactGenerate,
        review_feedback: str,
        count: int,
) -> list[dict[str, Any]]:
    """
    分批生成并清洗测验题目
    :param client: DeepSeek客户端
    :param notebook_title: 笔记本标题
    :param messages: 最近对话消息
    :param profile: 学生画像
    :param request: Studio生成请求
    :param review_feedback: 质检改进意见
    :param count: 目标题目数
    :return:
    """
    items: list[dict[str, Any]] = []
    max_attempts = (count // QUIZ_BATCH_SIZE) + 4
    while len(items) < count and max_attempts > 0:
        max_attempts -= 1
        batch_count = min(QUIZ_BATCH_SIZE, count - len(items))
        payload = await client.json_completion(
            system_prompt=_make_quiz_batch_system_prompt(
                count=batch_count,
                difficulty=request.difficulty,
                language=request.language,
            ),
            user_prompt=_make_batch_user_prompt(
                notebook_title=notebook_title,
                messages=messages,
                profile=profile,
                custom_prompt=request.custom_prompt,
                review_feedback=review_feedback,
                remaining=count - len(items),
                batch_count=batch_count,
                existing=_existing_item_keys(items, "question"),
            ),
            max_tokens=_structured_json_max_tokens(count=batch_count, per_item_tokens=170),
        )
        new_items = _sanitize_quiz_items(payload.get("items", []))
        _append_unique_items(
            target=items,
            candidates=new_items,
            key="question",
            limit=count,
        )
    if len(items) < count:
        raise ValueError(f"测验结构化JSON有效题目不足：需要{count}道，得到{len(items)}道")
    return items


async def _generate_flashcard_items(
        client: DeepSeekClient,
        notebook_title: str,
        messages: list[dict[str, str]],
        profile: ProfileData,
        request: StudioArtifactGenerate,
        review_feedback: str,
        count: int,
) -> list[dict[str, Any]]:
    """
    分批生成并清洗闪卡
    :param client: DeepSeek客户端
    :param notebook_title: 笔记本标题
    :param messages: 最近对话消息
    :param profile: 学生画像
    :param request: Studio生成请求
    :param review_feedback: 质检改进意见
    :param count: 目标闪卡数
    :return:
    """
    items: list[dict[str, Any]] = []
    max_attempts = (count // FLASHCARD_BATCH_SIZE) + 4
    while len(items) < count and max_attempts > 0:
        max_attempts -= 1
        batch_count = min(FLASHCARD_BATCH_SIZE, count - len(items))
        payload = await client.json_completion(
            system_prompt=_make_flashcard_batch_system_prompt(
                count=batch_count,
                difficulty=request.difficulty,
                language=request.language,
            ),
            user_prompt=_make_batch_user_prompt(
                notebook_title=notebook_title,
                messages=messages,
                profile=profile,
                custom_prompt=request.custom_prompt,
                review_feedback=review_feedback,
                remaining=count - len(items),
                batch_count=batch_count,
                existing=_existing_item_keys(items, "front"),
            ),
            max_tokens=_structured_json_max_tokens(count=batch_count, per_item_tokens=120),
        )
        new_items = _sanitize_flashcard_items(payload.get("items", []))
        _append_unique_items(
            target=items,
            candidates=new_items,
            key="front",
            limit=count,
        )
    if len(items) < count:
        raise ValueError(f"闪卡结构化JSON有效卡片不足：需要{count}张，得到{len(items)}张")
    return items


async def _generate_markdown_studio_artifact(
        client: DeepSeekClient,
        artifact_type: str,
        notebook_title: str,
        messages: list[dict[str, str]],
        profile: ProfileData,
        request: StudioArtifactGenerate,
        review_feedback: str,
) -> dict[str, Any]:
    """
    生成Markdown类Studio产物
    :param client: DeepSeek客户端
    :param artifact_type: Studio产物类型
    :param notebook_title: 笔记本标题
    :param messages: 最近对话消息
    :param profile: 学生画像
    :param request: Studio生成请求
    :param review_feedback: 质检改进意见
    :return:
    """
    spec = STUDIO_SPECS[artifact_type]
    system_prompt = f"""
你是学习Studio中的{spec.role}。
{spec.requirement}
如果最近对话中包含“知识库工具检索结果”，必须优先依据其中的内容生成；否则不得声称已经分析来源，不得伪造引用、页码或外部链接。
请根据笔记本主题、最近对话和用户补充要求生成内容。
只输出最终Markdown内容，不要解释生成过程，不要使用```markdown包裹整篇内容。
输出语言：{request.language}
"""
    content = await client.text_completion(
        system_prompt=system_prompt,
        user_prompt=_make_studio_user_prompt(
            notebook_title=notebook_title,
            messages=messages,
            profile=profile,
            custom_prompt=request.custom_prompt,
            review_feedback=review_feedback,
        ),
        max_tokens=2800,
    )
    return {
        "title": f"{notebook_title} · {spec.label}",
        "content": content,
        "artifact_data": {},
    }


def _make_studio_user_prompt(
        notebook_title: str,
        messages: list[dict[str, str]],
        profile: ProfileData,
        custom_prompt: str,
        review_feedback: str,
) -> str:
    """
    组装Studio生成提示词
    :param notebook_title: 笔记本标题
    :param messages: 最近对话消息
    :param profile: 学生画像
    :param custom_prompt: 用户补充要求
    :param review_feedback: 质检改进意见
    :return:
    """
    return (
        f"当前笔记本：{notebook_title}\n"
        f"当前学生画像：{json.dumps(profile.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"用户补充要求：{custom_prompt or '无'}\n"
        f"质检改进意见：{review_feedback or '无'}\n"
        "最近对话：\n"
        f"{json.dumps(messages[-12:], ensure_ascii=False)}"
    )


def _make_batch_user_prompt(
        notebook_title: str,
        messages: list[dict[str, str]],
        profile: ProfileData,
        custom_prompt: str,
        review_feedback: str,
        remaining: int,
        batch_count: int,
        existing: list[str],
) -> str:
    """
    组装分批结构化产物生成提示词
    :param notebook_title: 笔记本标题
    :param messages: 最近对话消息
    :param profile: 学生画像
    :param custom_prompt: 用户补充要求
    :param review_feedback: 质检改进意见
    :param remaining: 剩余需要数量
    :param batch_count: 本批数量
    :param existing: 已生成条目
    :return:
    """
    base_prompt = _make_studio_user_prompt(
        notebook_title=notebook_title,
        messages=messages,
        profile=profile,
        custom_prompt=custom_prompt,
        review_feedback=review_feedback,
    )
    return (
        f"{base_prompt}\n"
        f"本批生成要求：还需要{remaining}项，本批只生成{batch_count}项。\n"
        f"已生成条目不要重复：{json.dumps(existing[-40:], ensure_ascii=False)}"
    )


def _make_quiz_batch_system_prompt(count: int, difficulty: str, language: str) -> str:
    """
    构造测验分批JSON提示词
    :param count: 本批数量
    :param difficulty: 难度
    :param language: 输出语言
    :return:
    """
    return f"""
你是学习Studio中的测验生成智能体。
本批只生成{count}道单项选择题，难度为{difficulty}。
出题时理解用户真正想练习的能力点，不要只按表面关键词出题。
如果最近对话中包含“知识库工具检索结果”，必须优先依据其中的内容出题；否则不得声称已经分析来源，不得伪造引用。
必须输出合法json对象，不要输出json以外的文本。
所有字符串必须是一行短文本，不要在字符串内部换行，不要使用未转义双引号。
json格式：
{{
  "items": [
    {{
      "question": "题目",
      "options": ["A. 选项", "B. 选项", "C. 选项", "D. 选项"],
      "answer": 0,
      "explanation": "答案解析"
    }}
  ]
}}
answer必须是正确选项在options数组中的下标，范围为0到3。
输出语言：{language}
"""


def _make_flashcard_batch_system_prompt(count: int, difficulty: str, language: str) -> str:
    """
    构造闪卡分批JSON提示词
    :param count: 本批数量
    :param difficulty: 难度
    :param language: 输出语言
    :return:
    """
    return f"""
你是学习Studio中的闪卡生成智能体。
本批只生成{count}张问答闪卡，难度为{difficulty}。
先判断最适合做成正反面复习的知识单位，再组织卡片。遇到词汇、术语、概念、公式、事实或容易混淆的知识点，应优先拆成可翻面复习的卡片，而不是整理成普通长列表。
如果最近对话中包含“知识库工具检索结果”，必须优先依据其中的内容生成闪卡；否则不得声称已经分析来源，不得伪造引用。
必须输出合法json对象，不要输出json以外的文本。
所有字符串必须是一行短文本，不要在字符串内部换行，不要使用未转义双引号。
json格式：
{{
  "items": [
    {{
      "front": "卡片正面问题",
      "back": "卡片背面答案",
      "explanation": "补充说明"
    }}
  ]
}}
输出语言：{language}
"""


def _resolve_item_count(
        request: StudioArtifactGenerate,
        default_counts: dict[str, int],
        max_count: int,
) -> int:
    """
    解析测验/闪卡数量，明确数量优先于三档默认值
    :param request: Studio生成请求
    :param default_counts: 三档数量默认值
    :param max_count: 单次生成上限
    :return:
    """
    explicit_count = _extract_explicit_count(request.custom_prompt)
    if explicit_count is None:
        return default_counts[request.quantity]
    return max(1, min(explicit_count, max_count))


def _extract_explicit_count(text: str) -> int | None:
    """
    从用户原始要求中提取带单位的明确数量，避免把CET-6这类级别误当数量
    :param text: 用户补充要求
    :return:
    """
    match = EXPLICIT_COUNT_PATTERN.search(text or "")
    if not match:
        return None
    return int(match.group(1))


def _structured_json_max_tokens(count: int, per_item_tokens: int) -> int:
    """
    按结构化条目数量提高JSON输出预算，避免大批量闪卡/测验被截断
    :param count: 条目数量
    :param per_item_tokens: 每个条目的粗略token预算
    :return:
    """
    return min(8192, max(2800, 900 + count * per_item_tokens))


def _sanitize_quiz_items(raw_items: Any) -> list[dict[str, Any]]:
    """
    规整测验题目字段
    :param raw_items: 模型返回条目
    :return:
    """
    if not isinstance(raw_items, list):
        return []
    items = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        question = _clean_item_text(raw_item.get("question"))
        options = [
            _clean_item_text(option)
            for option in raw_item.get("options", [])
        ]
        options = [option for option in options if option]
        answer = _normalize_quiz_answer(raw_item.get("answer"))
        explanation = _clean_item_text(raw_item.get("explanation"))
        if not question or len(options) != 4 or answer not in range(4):
            continue
        items.append({
            "question": question,
            "options": options,
            "answer": answer,
            "explanation": explanation,
        })
    return items


def _sanitize_flashcard_items(raw_items: Any) -> list[dict[str, str]]:
    """
    规整闪卡字段
    :param raw_items: 模型返回条目
    :return:
    """
    if not isinstance(raw_items, list):
        return []
    items = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        front = _clean_item_text(raw_item.get("front") or raw_item.get("question") or raw_item.get("word"))
        back = _clean_item_text(raw_item.get("back") or raw_item.get("answer") or raw_item.get("definition"))
        explanation = _clean_item_text(raw_item.get("explanation") or raw_item.get("example"))
        if not front or not back:
            continue
        items.append({
            "front": front,
            "back": back,
            "explanation": explanation,
        })
    return items


def _append_unique_items(
        target: list[dict[str, Any]],
        candidates: list[dict[str, Any]],
        key: str,
        limit: int,
) -> None:
    """
    追加不重复结构化条目
    :param target: 目标列表
    :param candidates: 候选条目
    :param key: 去重字段
    :param limit: 最大数量
    :return:
    """
    seen = {_dedupe_key(item.get(key)) for item in target}
    for item in candidates:
        if len(target) >= limit:
            return
        item_key = _dedupe_key(item.get(key))
        if not item_key or item_key in seen:
            continue
        target.append(item)
        seen.add(item_key)


def _existing_item_keys(items: list[dict[str, Any]], key: str) -> list[str]:
    """
    提取已有条目名称供模型避重
    :param items: 已生成条目
    :param key: 字段名
    :return:
    """
    return [
        _clean_item_text(item.get(key))
        for item in items
        if _clean_item_text(item.get(key))
    ]


def _clean_item_text(value: Any) -> str:
    """
    清洗模型生成的单行文本字段
    :param value: 原始值
    :return:
    """
    return " ".join(str(value or "").split()).strip()


def _dedupe_key(value: Any) -> str:
    """
    生成去重键
    :param value: 原始值
    :return:
    """
    return _clean_item_text(value).casefold()


def _normalize_quiz_answer(value: Any) -> int | None:
    """
    规整测验答案下标
    :param value: 原始答案
    :return:
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = str(value or "").strip().upper()
    if text.isdigit():
        return int(text)
    if text in {"A", "B", "C", "D"}:
        return ord(text) - ord("A")
    if text.startswith(("A.", "B.", "C.", "D.")):
        return ord(text[0]) - ord("A")
    return None
