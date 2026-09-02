from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_session
from app.utils import Error
from app.utils import get_token_sub
from main import app


class FakeEmailVerificationService:
    """测试用邮箱验证码服务。"""

    sent_codes: list[tuple[str, str]] = []

    async def send_code(self, email: str, purpose: str) -> int:
        """
        记录发码请求
        :param email: 邮箱
        :param purpose: 用途
        :return: 有效期秒数
        """
        self.sent_codes.append((email, purpose))
        return 300

    async def verify_code(self, email: str, purpose: str, code: str) -> None:
        """
        校验固定测试验证码
        :param email: 邮箱
        :param purpose: 用途
        :param code: 验证码
        :return:
        """
        if code != "123456":
            raise Error(code=400, message="验证码错误")


@pytest.fixture(autouse=True)
def fake_email_verification_service(monkeypatch):
    FakeEmailVerificationService.sent_codes.clear()
    monkeypatch.setattr(
        "app.service.user.EmailVerificationService",
        FakeEmailVerificationService,
    )
    return FakeEmailVerificationService


@pytest.mark.asyncio
async def test_register_and_login(tmp_path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'test_auth.db'}"
    engine = create_async_engine(url=database_url)
    session_local = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_local() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            register_code_response = await client.post(
                "/api/auth/email-code",
                json={
                    "email": "test@example.com",
                    "purpose": "register",
                },
            )
            assert register_code_response.status_code == 200
            assert register_code_response.json() == {
                "errcode": 0,
                "email": "test@example.com",
                "expires_in": 300,
            }

            register_response = await client.post(
                "/api/auth/register",
                json={
                    "username": "test",
                    "password": "123456",
                    "confirm_password": "123456",
                    "email": "test@example.com",
                    "email_code": "123456",
                },
            )
            assert register_response.status_code == 200
            assert register_response.json() == {
                "errcode": 0,
                "username": "test",
            }

            login_response = await client.post(
                "/api/auth/login",
                json={
                    "username": "test",
                    "password": "123456",
                },
            )
            assert login_response.status_code == 200
            assert login_response.json()["errcode"] == 0
            assert get_token_sub(login_response.json()["token"]) == "test"

            token = login_response.json()["token"]
            me_response = await client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert me_response.status_code == 200
            assert me_response.json() == {
                "errcode": 0,
                "username": "test",
                "nickname": "test",
                "email": "test@example.com",
                "signature": "",
            }

            signature_response = await client.put(
                "/api/auth/me/signature",
                json={
                    "signature": "保持学习，持续迭代",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            assert signature_response.status_code == 200
            assert signature_response.json() == {
                "errcode": 0,
                "username": "test",
                "nickname": "test",
                "email": "test@example.com",
                "signature": "保持学习，持续迭代",
            }

            login_code_response = await client.post(
                "/api/auth/email-code",
                json={
                    "email": "test@example.com",
                    "purpose": "login",
                },
            )
            assert login_code_response.status_code == 200

            email_login_response = await client.post(
                "/api/auth/login/email",
                json={
                    "email": "test@example.com",
                    "email_code": "123456",
                },
            )
            assert email_login_response.status_code == 200
            assert email_login_response.json()["errcode"] == 0
            assert get_token_sub(email_login_response.json()["token"]) == "test"

            wrong_password_response = await client.post(
                "/api/auth/login",
                json={
                    "username": "test",
                    "password": "654321",
                },
            )
            assert wrong_password_response.status_code == 400
            assert wrong_password_response.json()["detail"]["message"] == "用户名或密码错误"

            duplicate_response = await client.post(
                "/api/auth/register",
                json={
                    "username": "test",
                    "password": "123456",
                    "confirm_password": "123456",
                    "email": "another@example.com",
                    "email_code": "123456",
                },
            )
            assert duplicate_response.status_code == 400
            assert duplicate_response.json()["detail"]["message"] == "用户名已存在"
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_register_password_mismatch(tmp_path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'test_password_mismatch.db'}"
    engine = create_async_engine(url=database_url)
    session_local = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_local() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/auth/register",
                json={
                    "username": "test",
                    "password": "123456",
                    "confirm_password": "654321",
                    "email": "test@example.com",
                    "email_code": "123456",
                },
            )
            assert response.status_code == 400
            assert response.json()["detail"]["message"] == "两次输入的密码不一致"
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
