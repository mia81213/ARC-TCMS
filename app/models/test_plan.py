"""测试计划 ORM 模型"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlanStatusEnum(str, enum.Enum):
    """计划状态"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TestPlan(Base):
    """测试计划"""

    __tablename__ = "test_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, comment="计划名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="描述")
    status: Mapped[PlanStatusEnum] = mapped_column(
        Enum(PlanStatusEnum), nullable=False, default=PlanStatusEnum.DRAFT, comment="状态"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    # 关联
    items: Mapped[list["TestPlanItem"]] = relationship(
        "TestPlanItem", back_populates="test_plan", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<TestPlan(id={self.id}, name='{self.name}')>"
