# -*- coding: utf-8 -*-
"""邮箱验证码生成、发送、校验和限流服务。"""

import json
import secrets
from typing import Literal

from app.core import redis_client, settings
from app.service.email import EmailService
from app.utils.error import Error

EmailCodePurpose = Literal["login", "register"]


class EmailVerificationService:
    """邮箱验证码服务。"""

    def __init__(self, email_service: EmailService | None = None):
        """
        初始化邮箱验证码服务
        :param email_service: 邮件服务
        :return:
        """
        self.email_service = email_service or EmailService()
        self.redis = redis_client

    async def send_code(self, email: str, purpose: EmailCodePurpose) -> int:
        """
        生成、缓存并发送验证码
        :param email: 邮箱
        :param purpose: 用途
        :return: 验证码有效期秒数
        """
        email = self._normalize_email(email)
        self._validate_purpose(purpose)

        try:
            cooldown_key = self._cooldown_key(email=email, purpose=purpose)
            if await self.redis.exists(cooldown_key):
                raise Error(code=429, message="验证码发送过于频繁，请稍后再试")

            code = self._generate_code()
            code_key = self._code_key(email=email, purpose=purpose)
            payload = {
                "code": code,
                "attempts": 0,
            }
            await self.redis.set(
                code_key,
                json.dumps(payload, ensure_ascii=False),
                ex=settings.email_code_expire_seconds,
            )
            await self.redis.set(
                cooldown_key,
                "1",
                ex=settings.email_code_cooldown_seconds,
            )

            try:
                await self.email_service.send_verification_code(
                    to_email=email,
                    code=code,
                    purpose=purpose,
                )
            except Error:
                await self.redis.delete(code_key, cooldown_key)
                raise

            return settings.email_code_expire_seconds
        except Error:
            raise
        except Exception as exc:
            raise Error(code=500, message=f"验证码服务不可用：{exc}") from exc

    async def verify_code(self, email: str, purpose: EmailCodePurpose, code: str) -> None:
        """
        校验验证码，成功后删除验证码
        :param email: 邮箱
        :param purpose: 用途
        :param code: 用户输入的验证码
        :return:
        """
        email = self._normalize_email(email)
        self._validate_purpose(purpose)
        code = code.strip()
        if not code:
            raise Error(code=400, message="邮箱验证码不能为空")

        try:
            code_key = self._code_key(email=email, purpose=purpose)
            stored = await self.redis.get(code_key)
            if stored is None:
                raise Error(code=400, message="验证码不存在或已过期")

            try:
                payload = json.loads(stored)
            except json.JSONDecodeError as exc:
                await self.redis.delete(code_key)
                raise Error(code=400, message="验证码无效，请重新获取") from exc

            if str(payload.get("code")) == code:
                await self.redis.delete(code_key)
                return

            attempts = int(payload.get("attempts", 0)) + 1
            if attempts >= settings.email_code_max_attempts:
                await self.redis.delete(code_key)
                raise Error(code=400, message="验证码错误次数过多，请重新获取")

            payload["attempts"] = attempts
            ttl = await self.redis.ttl(code_key)
            await self.redis.set(
                code_key,
                json.dumps(payload, ensure_ascii=False),
                ex=max(ttl, 1),
            )
            raise Error(code=400, message="验证码错误")
        except Error:
            raise
        except Exception as exc:
            raise Error(code=500, message=f"验证码服务不可用：{exc}") from exc

    @staticmethod
    def _generate_code() -> str:
        """
        生成6位数字验证码
        :return:
        """
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def _normalize_email(email: str) -> str:
        """
        规范化并简单校验邮箱
        :param email: 邮箱
        :return:
        """
        normalized = email.strip().lower()
        if not normalized or "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise Error(code=400, message="请输入有效邮箱")
        return normalized

    @staticmethod
    def _validate_purpose(purpose: str) -> None:
        """
        校验验证码用途
        :param purpose: 用途
        :return:
        """
        if purpose not in {"login", "register"}:
            raise Error(code=400, message="验证码用途不合法")

    @staticmethod
    def _code_key(email: str, purpose: str) -> str:
        """
        生成验证码Redis键
        :param email: 邮箱
        :param purpose: 用途
        :return:
        """
        return f"email_code:{purpose}:{email}"

    @staticmethod
    def _cooldown_key(email: str, purpose: str) -> str:
        """
        生成发码冷却Redis键
        :param email: 邮箱
        :param purpose: 用途
        :return:
        """
        return f"email_code_cooldown:{purpose}:{email}"
