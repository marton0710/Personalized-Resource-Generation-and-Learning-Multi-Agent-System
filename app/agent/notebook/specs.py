# -*- coding: utf-8 -*-
"""Studio 应用规格、角色和工具映射定义。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class StudioSpec:
    """Studio工具规格。"""

    label: str
    role: str
    requirement: str
    structured: bool = False


STUDIO_SPECS = {
    "learning_path": StudioSpec(
        label="学习路径",
        role="个性化学习路径规划智能体",
        requirement="适合把学习目标拆成先后顺序、阶段安排和下一步行动，结合画像生成由浅入深的学习路径。",
        structured=True,
    ),
    "study_guide": StudioSpec(
        label="学习指南",
        role="课程讲解智能体",
        requirement="适合系统学习或讲解一个主题，生成结构清晰的学习指南，包含目标、重点概念、学习顺序、自检问题和术语表。",
    ),
    "briefing": StudioSpec(
        label="报告",
        role="拓展阅读智能体",
        requirement="适合需要背景扩展、深入阅读或主题综述的请求，生成有层次的报告，包含摘要、核心观点、关键细节和后续建议。",
    ),
    "mindmap": StudioSpec(
        label="思维导图",
        role="思维导图智能体",
        requirement="适合呈现知识框架、层级结构、概念关系和章节脉络，生成可渲染的Mermaid mindmap代码，并在代码前补充一句简短说明。",
    ),
    "flashcards": StudioSpec(
        label="闪卡",
        role="知识巩固智能体",
        requirement="适合记忆、背诵、复习和快速自查，把单词、术语、概念、公式或事实组织成正反面问答闪卡。",
        structured=True,
    ),
    "quiz": StudioSpec(
        label="测验",
        role="练习题智能体",
        requirement="适合练习、自测、考察掌握程度或让学生被提问，生成单项选择题，覆盖基础理解、辨析和应用。",
        structured=True,
    ),
    "data_table": StudioSpec(
        label="数据表格",
        role="知识整理智能体",
        requirement="适合对照、比较、分类、参数归纳或结构化浏览，使用Markdown表格整理关键概念、解释、应用场景和注意事项。",
    ),
    "code_practice": StudioSpec(
        label="代码实操",
        role="代码实操智能体",
        requirement="适合把知识转化为可操作的编程练习或项目任务，生成可运行的代码实操案例，包含任务说明、示例代码、练习要求和检查清单。",
    ),
}

STUDIO_TOOL_ARTIFACT_TYPES = {
    f"generate_{artifact_type}": artifact_type
    for artifact_type in STUDIO_SPECS
}
