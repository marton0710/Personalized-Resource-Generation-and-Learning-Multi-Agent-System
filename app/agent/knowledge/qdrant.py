# -*- coding: utf-8 -*-
"""Qdrant collection、索引和底层查询操作。"""

from typing import Any, Literal

from qdrant_client import models

from .format import normalize_qdrant_hit
from .types import SOURCE_INDEX_FIELDS
from app.core import settings


class KnowledgeQdrantMixin:
    """Qdrant collection和查询底层操作。"""

    async def ensure_user_collection(self, collection_name: str, user_id: int, notebook_id: int) -> None:
        """
        确保用户笔记本collection存在且维度正确
        :param collection_name: collection名称
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :return:
        """
        if await self.client.collection_exists(collection_name):
            if await self._collection_vector_size(collection_name) == settings.knowledge_embedding_dimension:
                return
            await self.client.delete_collection(collection_name=collection_name, timeout=60)
        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=settings.knowledge_embedding_dimension,
                distance=models.Distance.COSINE,
            ),
            metadata={
                "source_scope": "user_pdf",
                "user_id": user_id,
                "notebook_id": notebook_id,
                "embedding_model": settings.knowledge_embedding_model,
                "vector_size": settings.knowledge_embedding_dimension,
            },
            timeout=60,
        )
        await self._create_payload_indexes(collection_name)

    async def delete_source(self, collection_name: str, source_id: int) -> None:
        """
        删除指定PDF来源在Qdrant中的全部切片
        :param collection_name: collection名称
        :param source_id: 来源id
        :return:
        """
        if not await self.client.collection_exists(collection_name):
            return
        await self.client.delete(
            collection_name=collection_name,
            points_selector=models.Filter(
                must=[
                    models.FieldCondition(
                        key="source_id",
                        match=models.MatchValue(value=source_id),
                    )
                ],
            ),
            wait=True,
        )

    async def delete_notebook_collection(self, user_id: int, notebook_id: int) -> None:
        """
        删除用户笔记本专属知识库collection
        :param user_id: 用户id
        :param notebook_id: 笔记本id
        :return:
        """
        collection_name = self.notebook_collection_name(
            user_id=user_id,
            notebook_id=notebook_id,
        )
        if await self.client.collection_exists(collection_name):
            await self.client.delete_collection(collection_name=collection_name, timeout=60)

    async def _query_collection(
            self,
            *,
            collection_name: str,
            query_vector: list[float],
            source_scope: Literal["user_pdf", "base"],
            limit: int,
    ) -> list[dict[str, Any]]:
        """
        查询单个Qdrant collection
        :param collection_name: collection名称
        :param query_vector: 查询向量
        :param source_scope: 来源范围
        :param limit: 最大返回数
        :return:
        """
        if limit <= 0 or not await self.client.collection_exists(collection_name):
            return []
        try:
            response = await self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                with_payload=True,
            )
        except Exception:
            return []
        hits = []
        for point in response.points:
            payload = point.payload or {}
            hits.append(normalize_qdrant_hit(
                payload=payload,
                score=float(point.score or 0),
                source_scope=source_scope,
            ))
        return hits

    async def _collection_vector_size(self, collection_name: str) -> int | None:
        """
        获取collection向量维度
        :param collection_name: collection名称
        :return:
        """
        info = await self.client.get_collection(collection_name=collection_name)
        vectors = info.config.params.vectors
        if isinstance(vectors, models.VectorParams):
            return int(vectors.size)
        if isinstance(vectors, dict) and "" in vectors:
            return int(vectors[""].size)
        return None

    async def _create_payload_indexes(self, collection_name: str) -> None:
        """
        创建用户PDF常用payload索引
        :param collection_name: collection名称
        :return:
        """
        for field_name, field_type in SOURCE_INDEX_FIELDS.items():
            await self.client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=field_type,
                wait=True,
            )
