# -*- coding: utf-8 -*-
"""笔记本受控文件路径和磁盘清理工具。"""

import asyncio
from pathlib import Path

from app.agent.knowledge import KnowledgeRetrievalAgent
from app.core import settings
from app.utils import Error


def get_stored_file(stored_path: str) -> Path:
    """
    获取受控的图片附件磁盘路径
    :param stored_path: 数据库中保存的相对路径
    :return:
    """
    upload_dir = Path(settings.chat_upload_dir).resolve()
    target = (upload_dir / stored_path).resolve()
    if upload_dir not in target.parents:
        raise Error(code=500, message="附件存储路径无效")
    return target


async def delete_stored_file(stored_path: str) -> None:
    """
    尽力删除图片附件磁盘文件
    :param stored_path: 数据库中保存的相对路径
    :return:
    """
    try:
        target = get_stored_file(stored_path=stored_path)
        await asyncio.to_thread(target.unlink, missing_ok=True)
    except (Error, OSError):
        return


def get_source_file(stored_path: str) -> Path:
    """
    获取受控的PDF来源磁盘路径
    :param stored_path: 数据库中保存的相对路径
    :return:
    """
    upload_dir = Path(settings.knowledge_upload_dir).resolve()
    target = (upload_dir / stored_path).resolve()
    if upload_dir not in target.parents:
        raise Error(code=500, message="PDF来源存储路径无效")
    return target


async def delete_source_file(stored_path: str) -> None:
    """
    尽力删除PDF来源磁盘文件
    :param stored_path: 数据库中保存的相对路径
    :return:
    """
    try:
        target = get_source_file(stored_path=stored_path)
        await asyncio.to_thread(target.unlink, missing_ok=True)
    except (Error, OSError):
        return


async def cleanup_source_vectors(collection_name: str, source_id: int) -> None:
    """
    入库失败时尽力清理已写入的向量切片
    :param collection_name: collection名称
    :param source_id: 来源id
    :return:
    """
    try:
        knowledge_agent = KnowledgeRetrievalAgent()
        await knowledge_agent.delete_source(
            collection_name=collection_name,
            source_id=source_id,
        )
    except Exception:
        return
