"""测试用例 ORM 模型"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriorityEnum(str, enum.Enum):
    """用例优先级"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class CaseStatusEnum(str, enum.Enum):
    """用例状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class TestCase(Base):
    """测试用例"""

    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="用例标题")
    module: Mapped[str] = mapped_column(String(128), nullable=False, index=True, comment="所属模块")
    priority: Mapped[PriorityEnum] = mapped_column(
        Enum(PriorityEnum), nullable=False, default=PriorityEnum.P2, comment="优先级"
    )
    status: Mapped[CaseStatusEnum] = mapped_column(
        Enum(CaseStatusEnum), nullable=False, default=CaseStatusEnum.DRAFT, comment="状态"
    )
    precondition: Mapped[str | None] = mapped_column(Text, nullable=True, comment="前置条件")
    steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list, comment="测试步骤")
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list, comment="标签")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def __repr__(self) -> str:
        return f"<TestCase(id={self.id}, title='{self.title}')>"
