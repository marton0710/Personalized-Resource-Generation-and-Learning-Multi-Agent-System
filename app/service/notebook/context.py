# -*- coding: utf-8 -*-
"""笔记本智能体上下文组装工具。"""

from app.db.model import NotebookAttachment, NotebookMessage, NotebookSource


def make_agent_messages(
        messages: list[NotebookMessage],
        message_attachments: dict[int, list[NotebookAttachment]],
) -> list[dict[str, str]]:
    """
    组装包含图片解析结果的智能体消息
    :param messages: 中央对话消息
    :param message_attachments: 按消息分组的图片附件
    :return:
    """
    rows = []
    for message in messages:
        content = message.content
        attachments = message_attachments.get(message.id, [])
        if attachments:
            attachment_context = "\n\n".join(
                (
                    f"附件：{attachment.original_name}\n"
                    "附件类型：图片解析结果\n"
                    f"{attachment.extracted_content}"
                )
                for attachment in attachments
            )
            content = f"{content}\n\n[本轮上传附件]\n{attachment_context}"
        rows.append({
            "role": message.role,
            "content": content,
        })
    return rows


def make_source_summary(sources: list[NotebookSource]) -> str:
    """
    组装当前笔记本PDF来源概况，供DeepSeek判断是否需要主动检索
    :param sources: PDF来源列表
    :return:
    """
    if not sources:
        return "当前笔记本没有用户上传PDF来源；系统基础知识库可通过 search_base_knowledge 检索。"
    rows = [
        "当前笔记本已有用户PDF来源，可通过 search_user_sources 检索；系统基础知识库可通过 search_base_knowledge 检索。"
    ]
    for index, source in enumerate(sources, start=1):
        rows.append(
            (
                f"{index}. {source.original_name}："
                f"{source.file_size / 1024 / 1024:.1f}MB，"
                f"{source.page_count or 0}页，"
                f"{source.chunk_count or 0}段，"
                f"文本页{source.text_page_count or 0}，"
                f"OCR页{source.ocr_page_count or 0}，"
                f"状态{source.status}"
            )
        )
    return "\n".join(rows)
