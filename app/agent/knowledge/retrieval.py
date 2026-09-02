# -*- coding: utf-8 -*-
"""知识库检索智能体，封装用户 PDF 与基础库检索。"""

from pathlib import Path
from typing import Any

from qdrant_client import AsyncQdrantClient, models

from .format import format_knowledge_context, make_point_id
from .pdf import extract_pdf_chunks
from .qdrant import KnowledgeQdrantMixin
from .types import (
    DEFAULT_BASE_LIMIT,
    DEFAULT_USER_LIMIT,
    KnowledgeEmbeddingModel,
)
from app.core import settings
from app.utils import Error


class KnowledgeRetrievalAgent(KnowledgeQdrantMixin):
    """知识库检索智能体，负责用户PDF与基础库的Qdrant检索。"""

    def __init__(
            self,
            client: AsyncQdrantClient | None = None,
            embedding_model: KnowledgeEmbeddingModel | None = None,
    ):
        """
        初始化知识库检索智能体
        :param client: Qdrant客户端
        :param embedding_model: Embedding封装
        :return:
        """
        self.client = client or AsyncQdrantClient(url=settings.qdrant_url, timeout=30)
        self.embedding_model = embedding_model or KnowledgeEmbeddingModel()

    @staticmethod
    def notebook_collection_name(user_id: int, notebook_id: int) -> str:
        """
        生成用户笔记本专属知识库collection名称
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :return:
        """
        return f"zhidao_user_{user_id}_notebook_{notebook_id}_knowledge"

    async def ingest_pdf(
            self,
            *,
            user_id: int,
            notebook_id: int,
            source_id: int,
            file_path: Path,
            original_name: str,
    ) -> dict[str, int | str]:
        """
        解析PDF并写入用户笔记本专属Qdrant collection
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :param source_id: 来源id
        :param file_path: PDF磁盘路径
        :param original_name: 原始文件名
        :return:
        """
        extraction = await extract_pdf_chunks(file_path=file_path)
        if not extraction.chunks:
            raise Error(code=400, message="PDF中未提取到可入库文本")
        collection_name = self.notebook_collection_name(
            user_id=user_id,
            notebook_id=notebook_id,
        )
        await self.ensure_user_collection(
            collection_name=collection_name,
            user_id=user_id,
            notebook_id=notebook_id,
        )
        vectors = await self.embedding_model.embed_texts([
            chunk.text
            for chunk in extraction.chunks
        ])
        points = [
            models.PointStruct(
                id=make_point_id(f"{collection_name}:{source_id}:{chunk.chunk_index}"),
                vector=vector,
                payload={
                    "source_scope": "user_pdf",
                    "source_id": source_id,
                    "user_id": user_id,
                    "notebook_id": notebook_id,
                    "file_name": original_name,
                    "page": chunk.page,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "extraction_method": chunk.extraction_method,
                    "text": chunk.text,
                },
            )
            for chunk, vector in zip(extraction.chunks, vectors)
        ]
        for start in range(0, len(points), 64):
            await self.client.upsert(
                collection_name=collection_name,
                points=points[start:start + 64],
                wait=True,
            )
        return {
            "collection_name": collection_name,
            "page_count": extraction.page_count,
            "chunk_count": len(extraction.chunks),
            "text_page_count": extraction.text_page_count,
            "ocr_page_count": extraction.ocr_page_count,
            "extraction_method": extraction.extraction_method,
        }

    async def search(
            self,
            *,
            query: str,
            user_id: int | None,
            notebook_id: int | None,
            user_limit: int = DEFAULT_USER_LIMIT,
            base_limit: int = DEFAULT_BASE_LIMIT,
    ) -> dict[str, Any]:
        """
        检索用户PDF和基础知识库
        :param query: 检索问题
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :param user_limit: 用户PDF最大返回数
        :param base_limit: 基础库最大返回数
        :return:
        """
        vector = await self.embedding_model.embed_query(query)
        user_hits: list[dict[str, Any]] = []
        if user_id is not None and notebook_id is not None:
            user_hits = await self._query_collection(
                collection_name=self.notebook_collection_name(user_id, notebook_id),
                query_vector=vector,
                source_scope="user_pdf",
                limit=user_limit,
            )
        base_hits = await self._query_collection(
            collection_name=settings.qdrant_base_collection,
            query_vector=vector,
            source_scope="base",
            limit=base_limit,
        )
        hits = [*user_hits, *base_hits]
        return {
            "query": query,
            "hits": hits,
            "context": format_knowledge_context(hits),
        }

    async def search_user_sources(
            self,
            *,
            query: str,
            user_id: int | None,
            notebook_id: int | None,
            limit: int = DEFAULT_USER_LIMIT,
    ) -> dict[str, Any]:
        """
        只检索当前笔记本的用户PDF资料库
        :param query: 检索问题
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :param limit: 最大返回数
        :return:
        """
        if user_id is None or notebook_id is None:
            return {
                "query": query,
                "hits": [],
                "context": "当前笔记本没有可检索的用户PDF资料。",
            }
        vector = await self.embedding_model.embed_query(query)
        hits = await self._query_collection(
            collection_name=self.notebook_collection_name(user_id, notebook_id),
            query_vector=vector,
            source_scope="user_pdf",
            limit=limit,
        )
        return {
            "query": query,
            "hits": hits,
            "context": format_knowledge_context(hits),
        }

    async def search_base_knowledge(
            self,
            *,
            query: str,
            limit: int = DEFAULT_BASE_LIMIT,
    ) -> dict[str, Any]:
        """
        只检索系统基础知识库
        :param query: 检索问题
        :param limit: 最大返回数
        :return:
        """
        vector = await self.embedding_model.embed_query(query)
        hits = await self._query_collection(
            collection_name=settings.qdrant_base_collection,
            query_vector=vector,
            source_scope="base",
            limit=limit,
        )
        return {
            "query": query,
            "hits": hits,
            "context": format_knowledge_context(hits),
        }
