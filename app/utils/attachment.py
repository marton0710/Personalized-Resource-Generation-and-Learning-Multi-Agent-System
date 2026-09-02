# -*- coding: utf-8 -*-
"""上传图片和 PDF 文件安全校验工具。"""

from pathlib import Path

from app.utils.error import Error


IMAGE_EXTENSIONS = {
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
}
PDF_EXTENSIONS = {".pdf"}


def validate_image_attachment(filename: str, content_type: str, content: bytes) -> None:
    """
    校验中央对话图片附件
    :param filename: 原始文件名
    :param content_type: 图片MIME类型
    :param content: 图片二进制
    :return:
    """
    extension = Path(filename).suffix.lower()
    if extension not in IMAGE_EXTENSIONS or not content_type.startswith("image/"):
        raise Error(code=400, message="中央对话仅支持上传PNG、JPG、WEBP或GIF图片")
    signatures = (
        content.startswith(b"\x89PNG\r\n\x1a\n"),
        content.startswith(b"\xff\xd8\xff"),
        content.startswith((b"GIF87a", b"GIF89a")),
        content.startswith(b"RIFF") and content[8:12] == b"WEBP",
    )
    if not any(signatures):
        raise Error(code=400, message="图片内容校验失败")


def validate_pdf_source(filename: str, content_type: str, content: bytes) -> None:
    """
    校验笔记本知识库PDF来源
    :param filename: 原始文件名
    :param content_type: 文件MIME类型
    :param content: 文件二进制
    :return:
    """
    extension = Path(filename).suffix.lower()
    allowed_content_types = {
        "application/pdf",
        "application/octet-stream",
    }
    if extension not in PDF_EXTENSIONS or content_type not in allowed_content_types:
        raise Error(code=400, message="知识库来源仅支持PDF文件")
    if not content.startswith(b"%PDF-"):
        raise Error(code=400, message="PDF内容校验失败")
