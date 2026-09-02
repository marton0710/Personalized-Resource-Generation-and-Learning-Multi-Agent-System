# -*- coding: utf-8 -*-
"""学习论坛业务服务。"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import ForumComment, ForumPost, User
from app.db.repositories import ForumRepositories
from app.utils import Error


class ForumService:
    """独立论坛业务服务层"""

    def __init__(self, session: AsyncSession, current_user: User):
        """
        初始化论坛业务服务层
        :param session: 数据库会话
        :param current_user: 当前登录用户
        :return:
        """
        self.session = session
        self.current_user = current_user
        self.repo = ForumRepositories(session=session)

    @staticmethod
    def _dump_post(
            row: ForumPost,
            username: str,
            comment_count: int,
            like_count: int,
            liked: bool = False,
            view_count: int | None = None,
    ) -> dict[str, Any]:
        """
        序列化论坛帖子
        :param row: 帖子对象
        :param username: 发布者用户名
        :param comment_count: 评论数量
        :param like_count: 点赞数量
        :param liked: 当前用户是否点赞
        :param view_count: 指定浏览量
        :return:
        """
        return {
            "id": row.id,
            "username": username,
            "title": row.title,
            "content": row.content,
            "category": row.category,
            "view_count": row.view_count if view_count is None else view_count,
            "comment_count": comment_count,
            "like_count": like_count,
            "liked": liked,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    @staticmethod
    def _dump_comment(row: ForumComment, username: str) -> dict[str, Any]:
        """
        序列化论坛评论
        :param row: 评论对象
        :param username: 评论者用户名
        :return:
        """
        return {
            "id": row.id,
            "username": username,
            "content": row.content,
            "created_at": row.created_at,
        }

    async def create_post(
            self,
            title: str,
            content: str,
            category: str,
    ) -> dict[str, Any]:
        """
        创建论坛帖子
        :param title: 帖子标题
        :param content: 帖子正文
        :param category: 讨论分区
        :return:
        """
        row = await self.repo.create_post(
            user_id=self.current_user.id,
            title=title.strip(),
            content=content.strip(),
            category=category.strip(),
        )
        post = self._dump_post(
            row=row,
            username=self.current_user.username,
            comment_count=0,
            like_count=0,
        )
        await self.session.commit()
        return {
            "errcode": 0,
            "post": post,
        }

    async def list_posts(self, category: str = "", keyword: str = "") -> dict[str, Any]:
        """
        查询论坛帖子列表
        :param category: 讨论分区
        :param keyword: 搜索关键词
        :return:
        """
        rows = await self.repo.list_posts(
            category=category.strip(),
            keyword=keyword.strip(),
        )
        liked_post_ids = await self.repo.list_liked_post_ids(
            post_ids=[row.id for row, _, _, _ in rows],
            user_id=self.current_user.id,
        )
        return {
            "errcode": 0,
            "posts": [
                self._dump_post(
                    row=row,
                    username=username,
                    comment_count=comment_count,
                    like_count=like_count,
                    liked=row.id in liked_post_ids,
                )
                for row, username, comment_count, like_count in rows
            ],
        }

    async def get_post(self, post_id: int) -> dict[str, Any]:
        """
        获取论坛帖子详情并增加浏览量
        :param post_id: 帖子id
        :return:
        """
        row, username, comment_count, like_count = await self._get_post_summary(post_id=post_id)
        view_count = row.view_count + 1
        post_id = row.id
        post = self._dump_post(
            row=row,
            username=username,
            comment_count=comment_count,
            like_count=like_count,
            view_count=view_count,
        )
        await self.repo.increment_post_views(post_id=post_id)
        comments = await self.repo.list_comments(post_id=post_id)
        liked = await self.repo.get_like(
            post_id=post_id,
            user_id=self.current_user.id,
        )
        post["liked"] = liked is not None
        serialized_comments = [
            self._dump_comment(comment, comment_username)
            for comment, comment_username in comments
        ]
        await self.session.commit()
        return {
            "errcode": 0,
            "post": post,
            "comments": serialized_comments,
        }

    async def delete_post(self, post_id: int) -> dict[str, int]:
        """
        删除当前用户发布的论坛帖子
        :param post_id: 帖子id
        :return:
        """
        row = await self.repo.get_post(
            post_id=post_id,
            user_id=self.current_user.id,
        )
        if row is None:
            raise Error(code=404, message="可删除的帖子不存在")
        try:
            await self.repo.delete_post(post=row)
            await self.session.commit()
            return {"errcode": 0}
        except Exception as e:
            await self.session.rollback()
            raise Error(code=500, message=f"删除帖子失败：{e}") from e

    async def create_comment(self, post_id: int, content: str) -> dict[str, Any]:
        """
        创建论坛帖子评论
        :param post_id: 帖子id
        :param content: 评论正文
        :return:
        """
        await self._get_post_summary(post_id=post_id)
        row = await self.repo.create_comment(
            post_id=post_id,
            user_id=self.current_user.id,
            content=content.strip(),
        )
        comment = self._dump_comment(row=row, username=self.current_user.username)
        await self.session.commit()
        return {
            "errcode": 0,
            "comment": comment,
        }

    async def toggle_like(self, post_id: int) -> dict[str, Any]:
        """
        切换论坛帖子点赞状态
        :param post_id: 帖子id
        :return:
        """
        await self._get_post_summary(post_id=post_id)
        row = await self.repo.get_like(
            post_id=post_id,
            user_id=self.current_user.id,
        )
        if row is None:
            await self.repo.create_like(
                post_id=post_id,
                user_id=self.current_user.id,
            )
            liked = True
        else:
            await self.repo.delete_like(like=row)
            liked = False
        _, _, _, like_count = await self._get_post_summary(post_id=post_id)
        await self.session.commit()
        return {
            "errcode": 0,
            "liked": liked,
            "like_count": like_count,
        }

    async def _get_post_summary(self, post_id: int) -> tuple[ForumPost, str, int, int]:
        """
        获取存在的论坛帖子及互动统计
        :param post_id: 帖子id
        :return:
        """
        row = await self.repo.get_post_summary(post_id=post_id)
        if row is None:
            raise Error(code=404, message="帖子不存在")
        return row
