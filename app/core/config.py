# -*- coding: utf-8 -*-
"""项目环境变量配置和 settings 实例。"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """项目配置，从.env读取"""

    # 异步数据库
    database_url: str = "sqlite+aiosqlite:///./data/zhidao.db"

    # 数据库调试日志
    db_echo: bool = False

    # JWT相关
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 7 * 24 * 60

    # DeepSeek相关
    DEEPSEEK_APIKEY: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"

    # OpenAI兼容视觉模型，用于解析中央对话中上传的图片
    VISION_APIKEY: str = ""
    vision_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    vision_model: str = "qwen3-vl-flash"

    # 中央对话附件
    chat_upload_dir: str = "./data/uploads/chat"
    chat_attachment_max_bytes: int = 10 * 1024 * 1024

    # 知识库与Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_base_collection: str = "kaoyan_full_knowledge"
    knowledge_upload_dir: str = "./data/uploads/knowledge"
    knowledge_pdf_max_bytes: int = 10 * 1024 * 1024
    knowledge_pdf_max_files: int = 5
    knowledge_embedding_model: str = "BAAI/bge-small-zh-v1.5"
    knowledge_embedding_dimension: int = 512
    knowledge_embedding_device: str = "auto"

    # redis相关
    redis_host: str = "127.0.0.1"
    redis_port: str = "6379"
    redis_db: int = 0
    redis_password: str | None = None

    # 邮箱验证码
    email_code_expire_seconds: int = 5 * 60
    email_code_cooldown_seconds: int = 60
    email_code_max_attempts: int = 5

    # SMTP
    SMTP_USER: str = ""
    SMTP_KEY: str = ""
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USE_SSL: bool = True
    SMTP_USE_TLS: bool = False
    SMTP_FROM_NAME: str = "至道"

    # 读取.env，忽略额外字段
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
