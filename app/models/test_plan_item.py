"""测试计划项（关联表）ORM 模型"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExecutionStatusEnum(str, enum.Enum):
    """执行状态"""
    PASS = "pass"
    FAIL = "fail"
    NT = "nt"
    NA = "na"


class TestPlanItem(Base):
    """测试计划中的用例执行项"""

    __tablename__ = "test_plan_items"
    __table_args__ = (
        UniqueConstraint("test_plan_id", "test_case_id", name="uq_plan_case"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("test_plans.id", ondelete="CASCADE"), nullable=False, comment="测试计划ID"
    )
    test_case_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, comment="测试用例ID"
    )
    execution_status: Mapped[ExecutionStatusEnum | None] = mapped_column(
        Enum(ExecutionStatusEnum), nullable=True, default=None, comment="执行状态"
    )
    executed_by: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="执行人")
    actual_result: Mapped[str | None] = mapped_column(Text, nullable=True, comment="实际结果")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="执行时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="创建时间"
    )

    # 关联
    test_plan: Mapped["TestPlan"] = relationship("TestPlan", back_populates="items")
    test_case: Mapped["TestCase"] = relationship("TestCase", lazy="selectin")

    def __repr__(self) -> str:
        return f"<TestPlanItem(id={self.id}, plan={self.test_plan_id}, case={self.test_case_id})>"
