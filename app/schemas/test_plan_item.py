"""测试计划项 Pydantic 模型"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.test_case import TestCaseResponse


class ExecutionStatusEnum(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NT = "nt"
    NA = "na"


class AddCasesRequest(BaseModel):
    """向计划批量添加用例的请求"""
    test_case_ids: list[int] = Field(..., min_length=1)


class UpdateExecutionRequest(BaseModel):
    """更新执行结果请求"""
    execution_status: ExecutionStatusEnum
    executed_by: str | None = Field(None, max_length=64)
    actual_result: str = Field(default="")
    notes: str = Field(default="")


class TestPlanItemResponse(BaseModel):
    """计划项的响应"""
    id: int
    test_plan_id: int
    test_case_id: int
    execution_status: ExecutionStatusEnum | None = None
    executed_by: str | None = None
    actual_result: str | None = None
    notes: str | None = None
    executed_at: datetime | None = None
    created_at: datetime
    test_case: TestCaseResponse | None = None

    model_config = {"from_attributes": True}
