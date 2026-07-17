"""测试用例路由 — API 和页面"""

import math

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.templates import templates
from app.schemas.test_case import (
    TestCaseCreate, TestCaseUpdate, TestCaseResponse, TestCaseListParams, PaginatedResponse,
)
from app.services import test_case_service as service

router = APIRouter(prefix="/api/test-cases", tags=["test-cases"])
page_router = APIRouter(prefix="/app/test-cases", tags=["pages-test-cases"])


# ═══════════════════════ API 端点 ═══════════════════════

@router.get("", response_model=PaginatedResponse)
async def list_test_cases_api(
    request: Request,
    params: TestCaseListParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """获取用例列表（JSON API）"""
    cases, total = await service.list_test_cases(db, params)
    total_pages = max(1, math.ceil(total / params.per_page))
    return PaginatedResponse(
        data=[TestCaseResponse.model_validate(c) for c in cases],
        meta={
            "page": params.page,
            "per_page": params.per_page,
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.get("/modules")
async def get_modules_api(db: AsyncSession = Depends(get_db)):
    """获取所有模块名"""
    modules = await service.get_modules(db)
    return {"data": modules}


@router.get("/tags")
async def get_tags_api(db: AsyncSession = Depends(get_db)):
    """获取所有标签"""
    tags = await service.get_tags(db)
    return {"data": tags}


@router.get("/{case_id}", response_model=TestCaseResponse)
async def get_test_case_api(case_id: int, db: AsyncSession = Depends(get_db)):
    """获取单个用例"""
    case = await service.get_test_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    return TestCaseResponse.model_validate(case)


@router.post("", response_model=TestCaseResponse, status_code=201)
async def create_test_case_api(data: TestCaseCreate, db: AsyncSession = Depends(get_db)):
    """创建用例"""
    case = await service.create_test_case(db, data)
    await db.commit()
    return TestCaseResponse.model_validate(case)


@router.put("/{case_id}", response_model=TestCaseResponse)
async def update_test_case_api(case_id: int, data: TestCaseUpdate, db: AsyncSession = Depends(get_db)):
    """更新用例"""
    case = await service.update_test_case(db, case_id, data)
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    await db.commit()
    return TestCaseResponse.model_validate(case)


@router.delete("/{case_id}")
async def delete_test_case_api(case_id: int, db: AsyncSession = Depends(get_db)):
    """删除用例"""
    success = await service.delete_test_case(db, case_id)
    if not success:
        raise HTTPException(status_code=404, detail="用例不存在")
    await db.commit()
    return {"data": None, "message": "删除成功"}


# ═══════════════════════ 页面路由 ═══════════════════════

@page_router.get("", response_class=HTMLResponse)
async def test_case_list_page(request: Request, db: AsyncSession = Depends(get_db)):
    """用例列表页"""
    modules = await service.get_modules(db)
    return templates.TemplateResponse(
        request, "pages/test_cases/list.html",
        {"modules": modules},
    )


@page_router.get("/new", response_class=HTMLResponse)
async def test_case_create_page(request: Request, db: AsyncSession = Depends(get_db)):
    """创建用例页"""
    modules = await service.get_modules(db)
    return templates.TemplateResponse(
        request, "pages/test_cases/form.html",
        {"case": None, "modules": modules, "is_new": True},
    )


@page_router.get("/{case_id}", response_class=HTMLResponse)
async def test_case_detail_page(case_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """用例详情页"""
    case = await service.get_test_case(db, case_id)
    if not case:
        return RedirectResponse(url="/app/test-cases", status_code=303)
    return templates.TemplateResponse(
        request, "pages/test_cases/detail.html",
        {"case": case},
    )


@page_router.get("/{case_id}/edit", response_class=HTMLResponse)
async def test_case_edit_page(case_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """编辑用例页"""
    case = await service.get_test_case(db, case_id)
    if not case:
        return RedirectResponse(url="/app/test-cases", status_code=303)
    modules = await service.get_modules(db)
    return templates.TemplateResponse(
        request, "pages/test_cases/form.html",
        {"case": case, "modules": modules, "is_new": False},
    )
