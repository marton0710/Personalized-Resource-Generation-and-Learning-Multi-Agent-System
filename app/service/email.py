# -*- coding: utf-8 -*-
"""SMTP 邮件发送服务。"""

import asyncio
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core import settings
from app.utils.error import Error


class EmailService:
    """SMTP邮件服务。"""

    async def send_verification_code(
            self,
            to_email: str,
            code: str,
            purpose: str,
    ) -> None:
        """
        发送邮箱验证码
        :param to_email: 收件邮箱
        :param code: 验证码
        :param purpose: 用途
        :return:
        """
        await asyncio.to_thread(
            self._send_verification_code,
            to_email,
            code,
            purpose,
        )

    def _send_verification_code(
            self,
            to_email: str,
            code: str,
            purpose: str,
    ) -> None:
        """
        使用同步SMTP客户端发送验证码
        :param to_email: 收件邮箱
        :param code: 验证码
        :param purpose: 用途
        :return:
        """
        if not settings.SMTP_USER or not settings.SMTP_KEY:
            raise Error(code=500, message="SMTP未配置，请检查SMTP_USER/SMTP_KEY")

        purpose_text = "登录" if purpose == "login" else "注册"
        message = EmailMessage()
        message["Subject"] = f"至道 {purpose_text}验证码"
        message["From"] = formataddr((settings.SMTP_FROM_NAME, settings.SMTP_USER))
        message["To"] = to_email
        message.set_content(
            "\n".join([
                f"你的至道 {purpose_text}验证码是：{code}",
                f"验证码{settings.email_code_expire_seconds // 60}分钟内有效。",
                "如果不是你本人操作，请忽略这封邮件。",
            ])
        )

        smtp_client = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP
        try:
            with smtp_client(
                    settings.SMTP_HOST,
                    settings.SMTP_PORT,
                    timeout=15,
            ) as client:
                if not settings.SMTP_USE_SSL and settings.SMTP_USE_TLS:
                    client.starttls()
                client.login(settings.SMTP_USER, settings.SMTP_KEY)
                client.send_message(message)
        except Error:
            raise
        except Exception as e:
            raise Error(code=500, message=f"邮件发送失败：{e}") from e
