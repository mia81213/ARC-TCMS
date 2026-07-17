"""测试计划路由 — API 和页面"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.templates import templates
from app.schemas.test_plan import TestPlanCreate, TestPlanUpdate, TestPlanResponse
from app.services import test_plan_service as service

router = APIRouter(prefix="/api/test-plans", tags=["test-plans"])
page_router = APIRouter(prefix="/app/test-plans", tags=["pages-test-plans"])


# ═══════════════════════ API 端点 ═══════════════════════

@router.get("")
async def list_test_plans_api(db: AsyncSession = Depends(get_db)):
    """获取计划列表"""
    plans = await service.list_test_plans(db)
    data = []
    for p in plans:
        summary = service.compute_summary(p.items)
        d = TestPlanResponse.model_validate(p)
        d.summary = summary
        data.append(d.model_dump())
    return {"data": data}


@router.get("/{plan_id}")
async def get_test_plan_api(plan_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个计划"""
    plan = await service.get_test_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    resp = TestPlanResponse.model_validate(plan)
    resp.summary = service.compute_summary(plan.items)
    return {"data": resp.model_dump()}


@router.post("", status_code=201)
async def create_test_plan_api(data: TestPlanCreate, db: AsyncSession = Depends(get_db)):
    """创建计划"""
    plan = await service.create_test_plan(db, data)
    await db.commit()
    return {"data": TestPlanResponse.model_validate(plan).model_dump()}


@router.put("/{plan_id}")
async def update_test_plan_api(plan_id: int, data: TestPlanUpdate, db: AsyncSession = Depends(get_db)):
    """更新计划"""
    plan = await service.update_test_plan(db, plan_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    await db.commit()
    return {"data": TestPlanResponse.model_validate(plan).model_dump()}


@router.delete("/{plan_id}")
async def delete_test_plan_api(plan_id: int, db: AsyncSession = Depends(get_db)):
    """删除计划"""
    success = await service.delete_test_plan(db, plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="计划不存在")
    await db.commit()
    return {"data": None, "message": "删除成功"}


# ═══════════════════════ 页面路由 ═══════════════════════

@page_router.get("", response_class=HTMLResponse)
async def test_plan_list_page(request: Request):
    """计划列表页"""
    return templates.TemplateResponse(
        request, "pages/test_plans/list.html", {}
    )


@page_router.get("/new", response_class=HTMLResponse)
async def test_plan_create_page(request: Request):
    """创建计划页 — 从用例类别中选择"""
    return templates.TemplateResponse(
        request, "pages/test_plans/form.html",
        {},
    )


@page_router.get("/{plan_id}", response_class=HTMLResponse)
async def test_plan_detail_page(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """计划详情页"""
    plan = await service.get_test_plan(db, plan_id)
    if not plan:
        return RedirectResponse(url="/app/test-plans", status_code=303)
    return templates.TemplateResponse(
        request, "pages/test_plans/detail.html",
        {"plan": plan},
    )


@page_router.get("/{plan_id}/edit", response_class=HTMLResponse)
async def test_plan_edit_page(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """编辑计划页 — 仅编辑名称"""
    plan = await service.get_test_plan(db, plan_id)
    if not plan:
        return RedirectResponse(url="/app/test-plans", status_code=303)
    return templates.TemplateResponse(
        request, "pages/test_plans/edit.html",
        {"plan": plan},
    )


@page_router.get("/{plan_id}/execute", response_class=HTMLResponse)
async def test_plan_execute_page(plan_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """逐条执行页 — 每页一条用例，左滑下一条"""
    plan = await service.get_test_plan(db, plan_id)
    if not plan:
        return RedirectResponse(url="/app/test-plans", status_code=303)
    return templates.TemplateResponse(
        request, "pages/test_plans/execute.html",
        {"plan": plan},
    )
