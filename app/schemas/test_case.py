"""测试用例 Pydantic 模型"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PriorityEnum(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class CaseStatusEnum(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class TestStep(BaseModel):
    """测试步骤"""
    seq: int = Field(..., description="步骤序号")
    action: str = Field("", description="操作描述")
    expected: str = Field("", description="预期结果")


class TestCaseBase(BaseModel):
    """用例基础字段"""
    title: str = Field(..., min_length=1, max_length=255, description="用例标题")
    module: str = Field(..., min_length=1, max_length=128, description="所属模块")
    priority: PriorityEnum = Field(default=PriorityEnum.P2, description="优先级")
    status: CaseStatusEnum = Field(default=CaseStatusEnum.DRAFT, description="状态")
    case_type: str = Field(default="test", description="用例类型: test / check")
    precondition: str = Field(default="", description="前置条件")
    steps: list[TestStep] = Field(default_factory=list, description="测试步骤")
    tags: list[str] = Field(default_factory=list, description="标签")
    check_category: str | None = Field(None, description="检查类别")
    check_criteria: str | None = Field(None, description="评价标准")
    check_result: str | None = Field(None, description="检查结果: pass/fail/nt/na")


class TestCaseCreate(TestCaseBase):
    """创建用例请求"""
    pass


class TestCaseUpdate(BaseModel):
    """更新用例请求（所有字段可选）"""
    title: str | None = Field(None, min_length=1, max_length=255)
    module: str | None = Field(None, min_length=1, max_length=128)
    priority: PriorityEnum | None = None
    status: CaseStatusEnum | None = None
    precondition: str | None = None
    steps: list[TestStep] | None = None
    tags: list[str] | None = None
    case_type: str | None = None
    check_category: str | None = None
    check_criteria: str | None = None
    check_result: str | None = None


class TestCaseResponse(TestCaseBase):
    """用例响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestCaseListParams(BaseModel):
    """用例列表查询参数"""
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")
    search: str | None = Field(None, description="搜索关键词（标题）")
    module: str | None = Field(None, description="模块筛选")
    priority: PriorityEnum | None = Field(None, description="优先级筛选")
    status: CaseStatusEnum | None = Field(None, description="状态筛选")
    case_type: str | None = Field(None, description="用例类型筛选")


class PaginatedResponse(BaseModel):
    """分页响应"""
    data: list
    meta: dict = Field(default_factory=lambda: {
        "page": 1, "per_page": 20, "total": 0, "total_pages": 0
    })
    message: str | None = None
    errors: list | None = None
