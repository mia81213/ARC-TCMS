"""测试计划 Pydantic 模型"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PlanStatusEnum(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TestPlanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    status: PlanStatusEnum = Field(default=PlanStatusEnum.DRAFT)


class TestPlanCreate(TestPlanBase):
    pass


class TestPlanUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    status: PlanStatusEnum | None = None


class TestPlanResponse(TestPlanBase):
    id: int
    created_at: datetime
    updated_at: datetime
    summary: dict = Field(default_factory=lambda: {"pass": 0, "fail": 0, "nt": 0, "na": 0, "untested": 0})

    model_config = {"from_attributes": True}
