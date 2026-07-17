"""应用配置"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置，从环境变量或 .env 文件读取"""

    DATABASE_URL: str = "sqlite+aiosqlite:///tcms.db"
    APP_TITLE: str = "测试用例管理系统"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
