# -*- coding: utf-8 -*-
"""用户注册、登录、会话和签名业务服务。"""

from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.model import User
from app.db.repositories import UserRepositories
from app.service.email_verification import EmailCodePurpose, EmailVerificationService
from app.utils import Error, create_access_token, hash_password, verify_password


class UserService:
    """用户服务层"""

    def __init__(
            self,
            session: AsyncSession,
            username: str = "",
            password: str = "",
            email: str | None = None,
            confirm_password: str | None = None,
            email_code: str | None = None,
    ):
        """
        初始化用户服务层
        :param session: 数据库会话
        :param username: 用户名
        :param password: 密码
        :param email: 邮箱
        :param confirm_password: 确认密码
        :return:
        """
        self.session = session
        self.username = username
        self.password = password
        self.email = email
        self.confirm_password = confirm_password
        self.email_code = email_code
        self.repo = UserRepositories(session=session)
        self.email_verification_service = EmailVerificationService()

    async def add_new_user(self) -> str:
        """
        添加新用户并返回username
        :return: username
        """
        if self.password != self.confirm_password:
            raise Error(code=400, message="两次输入的密码不一致")

        if self.email is None:
            raise Error(code=400, message="邮箱不能为空")

        if not self.email_code:
            raise Error(code=400, message="邮箱验证码不能为空")

        email = self.email.strip().lower()
        row = await self.repo.get_user_by_username_or_by_email(
            username=self.username,
            email=email,
        )
        if row:
            if row.username == self.username:
                raise Error(code=400, message="用户名已存在")
            elif row.email == email:
                raise Error(code=400, message="邮箱已存在")
            raise Error(code=400, message="用户已存在")

        await self.email_verification_service.verify_code(
            email=email,
            purpose="register",
            code=self.email_code,
        )

        try:
            new_user = await self.repo.create_user(
                username=self.username,
                password=hash_password(self.password),
                email=email,
            )
            await self.session.commit()
            return new_user.username
        except Exception as e:
            await self.session.rollback()
            raise Error(code=500, message=f"未知错误：{e}") from e

    async def send_email_code(self, purpose: EmailCodePurpose) -> int:
        """
        发送邮箱验证码
        :param purpose: 验证码用途
        :return: 有效期秒数
        """
        if self.email is None:
            raise Error(code=400, message="邮箱不能为空")

        email = self.email.strip().lower()
        row = await self.repo.get_user_by_email(email=email)
        if purpose == "login" and row is None:
            raise Error(code=400, message="邮箱未注册")
        if purpose == "register" and row is not None:
            raise Error(code=400, message="邮箱已存在")

        return await self.email_verification_service.send_code(
            email=email,
            purpose=purpose,
        )

    async def login(self) -> str:
        """
        登录
        :return: jwt token
        """
        row = await self.repo.get_user_by_username(username=self.username)

        if not row:
            raise Error(code=400, message="用户名或密码错误")

        if not verify_password(self.password, row.hashed_password):
            raise Error(code=400, message="用户名或密码错误")

        return await self._create_login_token(row)

    async def login_by_email_code(self) -> str:
        """
        邮箱验证码登录
        :return: jwt token
        """
        if self.email is None:
            raise Error(code=400, message="邮箱不能为空")
        if not self.email_code:
            raise Error(code=400, message="邮箱验证码不能为空")

        email = self.email.strip().lower()
        row = await self.repo.get_user_by_email(email=email)
        if row is None:
            raise Error(code=400, message="邮箱未注册")

        await self.email_verification_service.verify_code(
            email=email,
            purpose="login",
            code=self.email_code,
        )

        return await self._create_login_token(row)

    async def update_signature(self, row: User, signature: str) -> str:
        """
        更新用户个性签名
        :param row: 用户
        :param signature: 个性签名
        :return: 更新后的个性签名
        """
        normalized_signature = signature.strip()
        if len(normalized_signature) > 200:
            raise Error(code=400, message="个性签名不能超过200个字符")

        row.signature = normalized_signature
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise Error(code=500, message=f"更新个性签名失败：{e}") from e
        return row.signature

    async def _create_login_token(self, row: User) -> str:
        """
        更新会话并创建jwt
        :param row: 用户
        :return: jwt token
        """
        session_id = uuid4().hex
        row.active_session_id = session_id
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise Error(code=500, message=f"登录失败：{e}") from e

        return create_access_token(
            data={
                "sub": row.username,
                "sid": session_id,
            },
        )
