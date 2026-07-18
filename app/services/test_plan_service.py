"""测试计划业务逻辑"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.test_plan import TestPlan, PlanStatusEnum
from app.models.test_plan_item import TestPlanItem, ExecutionStatusEnum
from app.schemas.test_plan import TestPlanCreate, TestPlanUpdate


async def list_test_plans(db: AsyncSession, user_id: int | None = None) -> list[TestPlan]:
    """获取所有测试计划"""
    query = select(TestPlan).options(selectinload(TestPlan.items)).order_by(TestPlan.updated_at.desc())
    if user_id is not None:
        query = query.where(TestPlan.user_id == user_id)
    result = await db.execute(query)
    return list(result.scalars().all())


def compute_summary(items: list[TestPlanItem]) -> dict:
    """计算计划的执行汇总"""
    summary = {"pass": 0, "fail": 0, "nt": 0, "na": 0, "untested": 0}
    for item in items:
        if item.execution_status is None:
            summary["untested"] += 1
        else:
            summary[item.execution_status.value] += 1
    return summary


async def get_test_plan(db: AsyncSession, plan_id: int) -> TestPlan | None:
    """获取单个计划（含关联项）"""
    result = await db.execute(
        select(TestPlan)
        .options(selectinload(TestPlan.items).selectinload(TestPlanItem.test_case))
        .where(TestPlan.id == plan_id)
    )
    return result.scalar_one_or_none()


async def create_test_plan(db: AsyncSession, data: TestPlanCreate, user_id: int | None = None) -> TestPlan:
    """创建计划"""
    plan = TestPlan(
        user_id=user_id,
        name=data.name,
        description=data.description,
        status=PlanStatusEnum(data.status.value),
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


async def update_test_plan(db: AsyncSession, plan_id: int, data: TestPlanUpdate) -> TestPlan | None:
    """更新计划"""
    plan = await get_test_plan(db, plan_id)
    if not plan:
        return None

    update_data = data.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"] is not None:
        update_data["status"] = PlanStatusEnum(update_data["status"].value)

    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.flush()
    await db.refresh(plan)
    return plan


async def delete_test_plan(db: AsyncSession, plan_id: int) -> bool:
    """删除计划"""
    plan = await db.execute(select(TestPlan).where(TestPlan.id == plan_id))
    plan = plan.scalar_one_or_none()
    if not plan:
        return False
    await db.delete(plan)
    await db.flush()
    return True


# ── 计划项操作 ──

async def add_cases_to_plan(db: AsyncSession, plan_id: int, case_ids: list[int]) -> int:
    """向计划添加用例，返回实际新增数量"""
    # 获取已存在的 case_id
    existing_result = await db.execute(
        select(TestPlanItem.test_case_id).where(
            TestPlanItem.test_plan_id == plan_id,
            TestPlanItem.test_case_id.in_(case_ids),
        )
    )
    existing_ids = set(existing_result.scalars().all())

    added = 0
    for cid in case_ids:
        if cid not in existing_ids:
            db.add(TestPlanItem(test_plan_id=plan_id, test_case_id=cid))
            added += 1

    await db.flush()
    return added


async def remove_item_from_plan(db: AsyncSession, item_id: int) -> bool:
    """从计划中移除一个用例项"""
    item = await db.execute(select(TestPlanItem).where(TestPlanItem.id == item_id))
    item = item.scalar_one_or_none()
    if not item:
        return False
    await db.delete(item)
    await db.flush()
    return True


async def update_execution_result(
    db: AsyncSession, item_id: int, status: ExecutionStatusEnum,
    executed_by: str | None, actual_result: str, notes: str,
) -> TestPlanItem | None:
    """更新执行结果"""
    item = await db.execute(select(TestPlanItem).where(TestPlanItem.id == item_id))
    item = item.scalar_one_or_none()
    if not item:
        return None

    item.execution_status = status
    item.executed_by = executed_by
    item.actual_result = actual_result
    item.notes = notes
    item.executed_at = func.now()

    await db.flush()
    await db.refresh(item)
    return item


async def list_plan_items(db: AsyncSession, plan_id: int) -> list[TestPlanItem]:
    """列出计划中的所有项"""
    result = await db.execute(
        select(TestPlanItem)
        .options(selectinload(TestPlanItem.test_case))
        .where(TestPlanItem.test_plan_id == plan_id)
        .order_by(TestPlanItem.created_at)
    )
    return list(result.scalars().all())
