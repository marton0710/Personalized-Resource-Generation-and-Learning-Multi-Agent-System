# -*- coding: utf-8 -*-
"""PDF 文本抽取、扫描页 OCR 渲染和文本切块逻辑。"""

import asyncio
import re
from pathlib import Path

from pypdf import PdfReader

from .types import (
    CHUNK_MAX_CHARS,
    CHUNK_OVERLAP_CHARS,
    MIN_EMBEDDED_TEXT_CHARS,
    PdfChunk,
    PdfExtractionResult,
)
from app.agent.vision import VisionClient


async def extract_pdf_chunks(file_path: Path) -> PdfExtractionResult:
    """
    提取PDF文本并按页切块，扫描页会渲染后使用视觉模型OCR
    :param file_path: PDF路径
    :return: PDF解析结果
    """
    embedded_pages, page_count = await asyncio.to_thread(extract_embedded_pdf_pages, file_path)
    chunks = []
    text_page_count = 0
    ocr_page_count = 0
    vision_client: VisionClient | None = None
    for page_index, embedded_text in embedded_pages:
        text = normalize_text(embedded_text)
        extraction_method = "embedded_text"
        if len(text) < MIN_EMBEDDED_TEXT_CHARS:
            if vision_client is None:
                vision_client = VisionClient()
            image_content = await asyncio.to_thread(render_pdf_page_to_png, file_path, page_index)
            text = normalize_text(await vision_client.describe_image(
                content=image_content,
                content_type="image/png",
            ))
            extraction_method = "vision_ocr"
        if not text:
            continue
        if extraction_method == "vision_ocr":
            ocr_page_count += 1
        else:
            text_page_count += 1
        chunks.extend(chunk_page_text(
            text=text,
            page=page_index,
            start_index=len(chunks),
            extraction_method=extraction_method,
        ))
    return PdfExtractionResult(
        chunks=chunks,
        page_count=page_count,
        text_page_count=text_page_count,
        ocr_page_count=ocr_page_count,
    )


def extract_embedded_pdf_pages(file_path: Path) -> tuple[list[tuple[int, str]], int]:
    """
    同步提取PDF内嵌文本，调用方需要放入线程池
    :param file_path: PDF路径
    :return:
    """
    reader = PdfReader(str(file_path))
    pages = [
        (page_index, page.extract_text() or "")
        for page_index, page in enumerate(reader.pages, start=1)
    ]
    return pages, len(reader.pages)


def render_pdf_page_to_png(file_path: Path, page_number: int) -> bytes:
    """
    同步渲染PDF页面为PNG，调用方需要放入线程池
    :param file_path: PDF路径
    :param page_number: 1-based页码
    :return:
    """
    import fitz

    with fitz.open(str(file_path)) as document:
        page = document.load_page(page_number - 1)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        return pixmap.tobytes("png")


def chunk_page_text(
        text: str,
        page: int,
        start_index: int,
        extraction_method: str,
) -> list[PdfChunk]:
    """
    将单页文本切为固定长度片段
    :param text: 页面文本
    :param page: 页码
    :param start_index: 全文起始切片序号
    :return:
    """
    if len(text) <= CHUNK_MAX_CHARS:
        return [
            PdfChunk(
                chunk_id=f"p{page}-c{start_index + 1}",
                text=text,
                page=page,
                chunk_index=start_index + 1,
                extraction_method=extraction_method,
            )
        ]
    chunks = []
    cursor = 0
    while cursor < len(text):
        end = min(len(text), cursor + CHUNK_MAX_CHARS)
        chunk_text = text[cursor:end].strip()
        if chunk_text:
            chunk_index = start_index + len(chunks) + 1
            chunks.append(PdfChunk(
                chunk_id=f"p{page}-c{chunk_index}",
                text=chunk_text,
                page=page,
                chunk_index=chunk_index,
                extraction_method=extraction_method,
            ))
        if end >= len(text):
            break
        cursor = max(end - CHUNK_OVERLAP_CHARS, cursor + 1)
    return chunks


def normalize_text(text: str) -> str:
    """
    规整PDF提取文本
    :param text: 原始文本
    :return:
    """
    return re.sub(r"\s+", " ", text).strip()
