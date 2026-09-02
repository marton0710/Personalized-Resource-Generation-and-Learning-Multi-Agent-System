# -*- coding: utf-8 -*-
"""笔记本图片附件数据库操作。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import NotebookAttachment


class NotebookAttachmentRepositoryMixin:
    """中央对话图片附件数据库操作。"""

    session: AsyncSession

    async def create_attachment(
            self,
            notebook_id: int,
            user_id: int,
            attachment_type: str,
            original_name: str,
            stored_path: str,
            content_type: str,
            file_size: int,
            extracted_content: str,
    ) -> NotebookAttachment:
        """
        创建中央对话图片附件
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :param attachment_type: 附件类型
        :param original_name: 原始文件名
        :param stored_path: 磁盘存储路径
        :param content_type: MIME类型
        :param file_size: 文件大小
        :param extracted_content: 图片解析文本
        :return:
        """
        row = NotebookAttachment(
            notebook_id=notebook_id,
            user_id=user_id,
            attachment_type=attachment_type,
            original_name=original_name,
            stored_path=stored_path,
            content_type=content_type,
            file_size=file_size,
            extracted_content=extracted_content,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_attachment_paths(self, notebook_id: int) -> list[str]:
        """
        查询笔记本图片附件的磁盘路径
        :param notebook_id: 笔记本id
        :return:
        """
        stmt = (
            select(NotebookAttachment.stored_path)
            .where(NotebookAttachment.notebook_id == notebook_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_attachment(
            self,
            attachment_id: int,
            notebook_id: int,
            user_id: int,
    ) -> NotebookAttachment | None:
        """
        查询尚未发送的指定图片附件
        :param attachment_id: 图片附件id
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(NotebookAttachment)
            .where(
                NotebookAttachment.id == attachment_id,
                NotebookAttachment.notebook_id == notebook_id,
                NotebookAttachment.user_id == user_id,
                NotebookAttachment.message_id.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pending_attachments(
            self,
            attachment_ids: list[int],
            notebook_id: int,
            user_id: int,
    ) -> list[NotebookAttachment]:
        """
        按提交顺序查询待发送图片附件
        :param attachment_ids: 图片附件id列表
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        if not attachment_ids:
            return []
        stmt = (
            select(NotebookAttachment)
            .where(
                NotebookAttachment.id.in_(attachment_ids),
                NotebookAttachment.notebook_id == notebook_id,
                NotebookAttachment.user_id == user_id,
                NotebookAttachment.message_id.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        rows = {
            row.id: row
            for row in result.scalars().all()
        }
        return [
            rows[attachment_id]
            for attachment_id in attachment_ids
            if attachment_id in rows
        ]

    async def list_unsent_attachments(
            self,
            notebook_id: int,
            user_id: int,
    ) -> list[NotebookAttachment]:
        """
        查询笔记本内尚未发送的图片附件
        :param notebook_id: 笔记本id
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(NotebookAttachment)
            .where(
                NotebookAttachment.notebook_id == notebook_id,
                NotebookAttachment.user_id == user_id,
                NotebookAttachment.message_id.is_(None),
            )
            .order_by(NotebookAttachment.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_message_attachments(
            self,
            message_ids: list[int],
    ) -> dict[int, list[NotebookAttachment]]:
        """
        按消息分组查询已发送图片附件
        :param message_ids: 消息id列表
        :return:
        """
        if not message_ids:
            return {}
        stmt = (
            select(NotebookAttachment)
            .where(NotebookAttachment.message_id.in_(message_ids))
            .order_by(NotebookAttachment.id.asc())
        )
        result = await self.session.execute(stmt)
        rows: dict[int, list[NotebookAttachment]] = {}
        for row in result.scalars().all():
            rows.setdefault(row.message_id, []).append(row)
        return rows

    async def bind_attachments_to_message(
            self,
            attachments: list[NotebookAttachment],
            message_id: int,
    ) -> None:
        """
        将图片附件绑定到用户消息
        :param attachments: 图片附件列表
        :param message_id: 消息id
        :return:
        """
        for row in attachments:
            row.message_id = message_id
        await self.session.flush()

    async def delete_attachment(self, attachment: NotebookAttachment) -> None:
        """
        删除图片附件记录
        :param attachment: 图片附件对象
        :return:
        """
        await self.session.delete(attachment)
        await self.session.flush()
