# -*- coding: utf-8 -*-
"""知识库检索入参、PDF 切片和 Embedding 类型定义。"""

import asyncio
from dataclasses import dataclass
from functools import lru_cache

from pydantic import BaseModel, Field
from qdrant_client import models
from sentence_transformers import SentenceTransformer

from app.core import settings
from app.utils import Error


CHUNK_MAX_CHARS = 900
CHUNK_OVERLAP_CHARS = 120
MIN_EMBEDDED_TEXT_CHARS = 80
DEFAULT_USER_LIMIT = 5
DEFAULT_BASE_LIMIT = 5

SOURCE_INDEX_FIELDS = {
    "source_scope": models.PayloadSchemaType.KEYWORD,
    "source_id": models.PayloadSchemaType.INTEGER,
    "user_id": models.PayloadSchemaType.INTEGER,
    "notebook_id": models.PayloadSchemaType.INTEGER,
    "file_name": models.PayloadSchemaType.KEYWORD,
    "page": models.PayloadSchemaType.INTEGER,
}


class KnowledgeSearchArgs(BaseModel):
    """LangChain知识库检索工具参数。"""

    query: str = Field(..., min_length=1, max_length=1000, description="需要检索的学习问题或关键词")


@dataclass
class PdfChunk:
    """PDF切片结果。"""

    chunk_id: str
    text: str
    page: int
    chunk_index: int
    extraction_method: str


@dataclass
class PdfExtractionResult:
    """PDF解析结果。"""

    chunks: list[PdfChunk]
    page_count: int
    text_page_count: int
    ocr_page_count: int

    @property
    def extraction_method(self) -> str:
        """
        返回PDF整体解析方式
        :return:
        """
        if self.text_page_count and self.ocr_page_count:
            return "mixed"
        if self.ocr_page_count:
            return "vision_ocr"
        return "embedded_text"


class KnowledgeEmbeddingModel:
    """BGE中文Embedding封装，确保基础库和用户PDF使用同一向量空间。"""

    def __init__(
            self,
            model_name: str | None = None,
            device: str | None = None,
    ):
        """
        初始化Embedding模型
        :param model_name: SentenceTransformer模型名称
        :param device: 运行设备，auto/cpu/cuda
        :return:
        """
        self.model_name = model_name or settings.knowledge_embedding_model
        self.device = self._resolve_device(device or settings.knowledge_embedding_device)
        self.model = _load_sentence_transformer(self.model_name, self.device)
        dimension = self.get_dimension()
        if dimension != settings.knowledge_embedding_dimension:
            raise Error(
                code=500,
                message=(
                    f"Embedding维度不一致：配置为{settings.knowledge_embedding_dimension}，"
                    f"模型实际为{dimension}"
                ),
            )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        批量生成归一化向量
        :param texts: 文本列表
        :return:
        """
        if not texts:
            return []
        vectors = await asyncio.to_thread(
            self.model.encode,
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]

    async def embed_query(self, query: str) -> list[float]:
        """
        生成查询向量
        :param query: 查询文本
        :return:
        """
        vectors = await self.embed_texts([query])
        return vectors[0]

    def get_dimension(self) -> int:
        """
        获取模型输出维度
        :return:
        """
        return int(self.model.get_embedding_dimension())

    @staticmethod
    def _resolve_device(device: str) -> str:
        """
        根据配置选择运行设备
        :param device: auto/cpu/cuda
        :return:
        """
        if device != "auto":
            return device
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"


@lru_cache(maxsize=4)
def _load_sentence_transformer(model_name: str, device: str) -> SentenceTransformer:
    """
    缓存加载SentenceTransformer模型
    :param model_name: 模型名称
    :param device: 运行设备
    :return:
    """
    try:
        return SentenceTransformer(
            model_name,
            device=device,
            local_files_only=True,
        )
    except Exception as exc:
        raise Error(
            code=500,
            message=f"加载Embedding模型失败：{model_name}，请确认模型已缓存到本机。错误：{exc}",
        ) from exc
