# -*- coding: utf-8 -*-
"""学习论坛数据库操作。"""

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import ForumComment, ForumPost, ForumPostLike, User


class ForumRepositories:
    """论坛数据库操作"""

    def __init__(self, session: AsyncSession):
        """
        初始化论坛数据库操作
        :param session: 数据库会话
        :return:
        """
        self.session = session

    @staticmethod
    def _post_summary_query():
        """组装帖子列表和详情共用统计查询。"""
        return (
            select(
                ForumPost,
                User.username,
                func.count(func.distinct(ForumComment.id)).label("comment_count"),
                func.count(func.distinct(ForumPostLike.id)).label("like_count"),
            )
            .join(User, User.id == ForumPost.user_id)
            .outerjoin(
                ForumComment,
                and_(
                    ForumComment.post_id == ForumPost.id,
                    ForumComment.status == "active",
                ),
            )
            .outerjoin(ForumPostLike, ForumPostLike.post_id == ForumPost.id)
            .group_by(ForumPost.id, User.username)
        )

    async def create_post(
            self,
            user_id: int,
            title: str,
            content: str,
            category: str,
    ) -> ForumPost:
        """
        创建论坛帖子
        :param user_id: 用户id
        :param title: 帖子标题
        :param content: 帖子正文
        :param category: 讨论分区
        :return:
        """
        row = ForumPost(
            user_id=user_id,
            title=title,
            content=content,
            category=category,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_posts(
            self,
            category: str = "",
            keyword: str = "",
            limit: int = 50,
    ) -> list[tuple[ForumPost, str, int, int]]:
        """
        查询论坛帖子列表及互动统计
        :param category: 讨论分区
        :param keyword: 搜索关键词
        :param limit: 最大返回数量
        :return:
        """
        stmt = (
            self._post_summary_query()
            .where(ForumPost.status == "active")
            .order_by(ForumPost.id.desc())
            .limit(limit)
        )
        if category:
            stmt = stmt.where(ForumPost.category == category)
        if keyword:
            stmt = stmt.where(
                or_(
                    ForumPost.title.contains(keyword),
                    ForumPost.content.contains(keyword),
                )
            )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_post_summary(self, post_id: int) -> tuple[ForumPost, str, int, int] | None:
        """
        查询论坛帖子及互动统计
        :param post_id: 帖子id
        :return:
        """
        stmt = (
            self._post_summary_query()
            .where(
                ForumPost.id == post_id,
                ForumPost.status == "active",
            )
        )
        result = await self.session.execute(stmt)
        return result.one_or_none()

    async def get_post(self, post_id: int, user_id: int) -> ForumPost | None:
        """
        查询用户发布的指定帖子
        :param post_id: 帖子id
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(ForumPost)
            .where(
                ForumPost.id == post_id,
                ForumPost.user_id == user_id,
                ForumPost.status == "active",
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_post(self, post: ForumPost) -> None:
        """
        删除论坛帖子
        :param post: 帖子对象
        :return:
        """
        await self.session.delete(post)
        await self.session.flush()

    async def increment_post_views(self, post_id: int) -> None:
        """
        增加帖子浏览量
        :param post_id: 帖子id
        :return:
        """
        stmt = (
            update(ForumPost)
            .where(ForumPost.id == post_id)
            .values(view_count=ForumPost.view_count + 1)
        )
        await self.session.execute(stmt)

    async def create_comment(self, post_id: int, user_id: int, content: str) -> ForumComment:
        """
        创建帖子评论
        :param post_id: 帖子id
        :param user_id: 用户id
        :param content: 评论正文
        :return:
        """
        row = ForumComment(
            post_id=post_id,
            user_id=user_id,
            content=content,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_comments(self, post_id: int) -> list[tuple[ForumComment, str]]:
        """
        查询帖子评论列表
        :param post_id: 帖子id
        :return:
        """
        stmt = (
            select(ForumComment, User.username)
            .join(User, User.id == ForumComment.user_id)
            .where(
                ForumComment.post_id == post_id,
                ForumComment.status == "active",
            )
            .order_by(ForumComment.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.all())

    async def get_like(self, post_id: int, user_id: int) -> ForumPostLike | None:
        """
        查询用户的帖子点赞记录
        :param post_id: 帖子id
        :param user_id: 用户id
        :return:
        """
        stmt = (
            select(ForumPostLike)
            .where(
                ForumPostLike.post_id == post_id,
                ForumPostLike.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_liked_post_ids(self, post_ids: list[int], user_id: int) -> set[int]:
        """
        查询用户已点赞的帖子id
        :param post_ids: 待查询帖子id
        :param user_id: 用户id
        :return:
        """
        if not post_ids:
            return set()
        stmt = (
            select(ForumPostLike.post_id)
            .where(
                ForumPostLike.post_id.in_(post_ids),
                ForumPostLike.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return set(result.scalars().all())

    async def create_like(self, post_id: int, user_id: int) -> ForumPostLike:
        """
        创建帖子点赞记录
        :param post_id: 帖子id
        :param user_id: 用户id
        :return:
        """
        row = ForumPostLike(
            post_id=post_id,
            user_id=user_id,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def delete_like(self, like: ForumPostLike) -> None:
        """
        删除帖子点赞记录
        :param like: 点赞记录
        :return:
        """
        await self.session.delete(like)
        await self.session.flush()
