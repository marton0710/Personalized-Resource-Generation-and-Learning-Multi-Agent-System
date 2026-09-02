# -*- coding: utf-8 -*-
"""知识库检索命中结果规整与上下文格式化工具。"""

import math
import uuid
from typing import Any, Literal


def make_point_id(value: str) -> str:
    """
    将业务id转换为稳定UUID
    :param value: 业务id
    :return:
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, value))


def normalize_qdrant_hit(
        *,
        payload: dict[str, Any],
        score: float,
        source_scope: Literal["user_pdf", "base"],
) -> dict[str, Any]:
    """
    将Qdrant命中规整为统一来源结构
    :param payload: Qdrant payload
    :param score: 相似度分数
    :param source_scope: 来源范围
    :return:
    """
    if source_scope == "user_pdf":
        return {
            "source_scope": "user_pdf",
            "source_label": "用户PDF",
            "score": score,
            "source_id": payload.get("source_id"),
            "title": payload.get("file_name") or "用户PDF",
            "page": payload.get("page"),
            "chunk_id": payload.get("chunk_id"),
            "text": payload.get("text") or "",
        }
    return {
        "source_scope": "base",
        "source_label": "基础知识库",
        "score": score,
        "source_id": payload.get("knowledge_id") or payload.get("point_id"),
        "title": payload.get("title") or payload.get("source_document") or "基础知识",
        "page": payload.get("source_pdf_page"),
        "chunk_id": payload.get("knowledge_id") or payload.get("code"),
        "text": (
            payload.get("content")
            or payload.get("retrieval_text")
            or payload.get("text_for_embedding")
            or ""
        ),
    }


def format_knowledge_context(hits: list[dict[str, Any]], max_chars: int = 5200) -> str:
    """
    将检索结果格式化为提示词上下文
    :param hits: 检索命中
    :param max_chars: 最大字符数
    :return:
    """
    if not hits:
        return "本轮没有检索到可用知识库片段。"
    sections = []
    used = 0
    for index, hit in enumerate(hits, start=1):
        text = str(hit.get("text") or "").strip()
        if not text:
            continue
        page = hit.get("page") or "未知"
        header = (
            f"【来源{index}｜{hit['source_label']}｜{hit.get('title')}｜"
            f"页码：{page}｜分数：{round_score(hit.get('score', 0))}】"
        )
        section = f"{header}\n{text[:900]}"
        if used + len(section) > max_chars:
            break
        sections.append(section)
        used += len(section)
    return "\n\n".join(sections) if sections else "本轮没有检索到可用知识库片段。"


def round_score(score: float) -> float:
    """
    规整相似度分数显示
    :param score: 原始分数
    :return:
    """
    if not math.isfinite(score):
        return 0.0
    return round(score, 4)
