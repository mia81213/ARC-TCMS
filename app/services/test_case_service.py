"""测试用例业务逻辑"""

import math

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_case import TestCase, PriorityEnum as OrmPriority, CaseStatusEnum as OrmStatus
from app.schemas.test_case import (
    TestCaseCreate, TestCaseUpdate, TestCaseListParams,
    PriorityEnum, CaseStatusEnum,
)


def _to_orm_priority(p: PriorityEnum) -> OrmPriority:
    return OrmPriority(p.value)


def _to_orm_status(s: CaseStatusEnum) -> OrmStatus:
    return OrmStatus(s.value)


async def list_test_cases(db: AsyncSession, params: TestCaseListParams) -> tuple[list[TestCase], int]:
    """列表查询，返回 (用例列表, 总数)"""
    query = select(TestCase)
    count_query = select(func.count(TestCase.id))

    # 类型筛选
    if params.case_type:
        query = query.where(TestCase.case_type == params.case_type)
        count_query = count_query.where(TestCase.case_type == params.case_type)

    # 搜索
    if params.search:
        like = f"%{params.search}%"
        query = query.where(TestCase.title.like(like))
        count_query = count_query.where(TestCase.title.like(like))

    # 模块筛选
    if params.module:
        query = query.where(TestCase.module == params.module)
        count_query = count_query.where(TestCase.module == params.module)

    # 优先级筛选
    if params.priority:
        query = query.where(TestCase.priority == _to_orm_priority(params.priority))
        count_query = count_query.where(TestCase.priority == _to_orm_priority(params.priority))

    # 状态筛选
    if params.status:
        query = query.where(TestCase.status == _to_orm_status(params.status))
        count_query = count_query.where(TestCase.status == _to_orm_status(params.status))

    # 分页
    offset = (params.page - 1) * params.per_page
    query = query.order_by(TestCase.updated_at.desc()).offset(offset).limit(params.per_page)

    result = await db.execute(query)
    cases = list(result.scalars().all())

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    return cases, total


async def get_test_case(db: AsyncSession, case_id: int) -> TestCase | None:
    """获取单个用例"""
    result = await db.execute(select(TestCase).where(TestCase.id == case_id))
    return result.scalar_one_or_none()


async def create_test_case(db: AsyncSession, data: TestCaseCreate) -> TestCase:
    """创建用例"""
    case = TestCase(
        title=data.title,
        module=data.module,
        priority=_to_orm_priority(data.priority),
        status=_to_orm_status(data.status),
        precondition=data.precondition,
        steps=[step.model_dump() for step in data.steps],
        tags=data.tags,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


async def update_test_case(db: AsyncSession, case_id: int, data: TestCaseUpdate) -> TestCase | None:
    """更新用例"""
    case = await get_test_case(db, case_id)
    if not case:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # 处理枚举字段
    if "priority" in update_data and update_data["priority"] is not None:
        update_data["priority"] = _to_orm_priority(update_data["priority"])
    if "status" in update_data and update_data["status"] is not None:
        update_data["status"] = _to_orm_status(update_data["status"])

    # 处理步骤：将 Pydantic 模型转为 dict 列表
    if "steps" in update_data and update_data["steps"] is not None:
        update_data["steps"] = [s.model_dump() if hasattr(s, 'model_dump') else s for s in update_data["steps"]]

    for key, value in update_data.items():
        setattr(case, key, value)

    await db.flush()
    await db.refresh(case)
    return case


async def delete_test_case(db: AsyncSession, case_id: int) -> bool:
    """删除用例，返回是否成功"""
    case = await get_test_case(db, case_id)
    if not case:
        return False
    await db.delete(case)
    await db.flush()
    return True


async def get_modules(db: AsyncSession) -> list[str]:
    """获取所有不重复的模块名"""
    result = await db.execute(select(TestCase.module).distinct().order_by(TestCase.module))
    return list(result.scalars().all())


async def get_tags(db: AsyncSession) -> list[str]:
    """获取所有不重复的标签"""
    cases_result = await db.execute(select(TestCase.tags))
    all_tags: set[str] = set()
    for row in cases_result.scalars().all():
        if row:
            for tag in row:
                all_tags.add(tag)
    return sorted(all_tags)
