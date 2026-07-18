"""数据库引擎和会话管理"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# 异步会话工厂
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """ORM 基类"""
    pass


async def get_db() -> AsyncSession:
    """FastAPI 依赖：获取数据库会话"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """初始化数据库，创建所有表并自动添加缺失列"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 自动迁移：为已有表添加新列
    migrations = {
        "test_cases": [
            ("case_type", "VARCHAR(16) NOT NULL DEFAULT 'test'"),
            ("check_category", "VARCHAR(128)"),
            ("check_criteria", "TEXT"),
            ("check_result", "VARCHAR(16)"),
            ("check_frequency", "VARCHAR(32)"),
            ("user_id", "INTEGER REFERENCES users(id)"),
        ],
        "test_plans": [
            ("user_id", "INTEGER REFERENCES users(id)"),
        ],
    }

    async with engine.begin() as conn:
        for table, columns in migrations.items():
            for col_name, col_def in columns:
                try:
                    await conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
                    )
                except Exception:
                    pass  # 列已存在则跳过
