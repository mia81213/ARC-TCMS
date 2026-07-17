"""测试计划项路由 — API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.test_plan_item import ExecutionStatusEnum as OrmExecStatus
from app.schemas.test_plan_item import (
    AddCasesRequest, UpdateExecutionRequest, TestPlanItemResponse,
)
from app.services import test_plan_service as plan_service

router = APIRouter(prefix="/api/test-plans", tags=["test-plan-items"])


@router.get("/{plan_id}/items")
async def list_plan_items_api(plan_id: int, db: AsyncSession = Depends(get_db)):
    """获取计划中的所有用例项"""
    items = await plan_service.list_plan_items(db, plan_id)
    return {"data": [TestPlanItemResponse.model_validate(item).model_dump() for item in items]}


@router.post("/{plan_id}/items", status_code=201)
async def add_cases_to_plan_api(plan_id: int, data: AddCasesRequest, db: AsyncSession = Depends(get_db)):
    """向计划批量添加用例"""
    added = await plan_service.add_cases_to_plan(db, plan_id, data.test_case_ids)
    await db.commit()
    return {"data": None, "message": f"成功添加 {added} 条用例（{len(data.test_case_ids) - added} 条已存在）"}


@router.delete("/{plan_id}/items/{item_id}")
async def remove_item_api(plan_id: int, item_id: int, db: AsyncSession = Depends(get_db)):
    """从计划中移除用例项"""
    success = await plan_service.remove_item_from_plan(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="项不存在")
    await db.commit()
    return {"data": None, "message": "移除成功"}


@router.put("/{plan_id}/items/{item_id}")
async def update_execution_api(
    plan_id: int, item_id: int, data: UpdateExecutionRequest, db: AsyncSession = Depends(get_db),
):
    """更新执行结果"""
    item = await plan_service.update_execution_result(
        db, item_id,
        status=OrmExecStatus(data.execution_status.value),
        executed_by=data.executed_by,
        actual_result=data.actual_result,
        notes=data.notes,
    )
    if not item:
        raise HTTPException(status_code=404, detail="项不存在")
    await db.commit()
    return {"data": TestPlanItemResponse.model_validate(item).model_dump(), "message": "执行结果已更新"}
