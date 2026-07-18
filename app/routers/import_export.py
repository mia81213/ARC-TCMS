"""导入导出路由 — API 和页面"""

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_optional_user
from app.models.user import User
from app.templates import templates
from app.services import import_export_service as service
from app.models.test_case import TestCase, PriorityEnum, CaseStatusEnum

router = APIRouter(prefix="/api", tags=["import-export"])
page_router = APIRouter(prefix="/app/import-export", tags=["pages-import-export"])


# ═══════════════════════ API 端点 ═══════════════════════

@router.get("/export/test-cases")
async def export_test_cases(
    module: str | None = Query(None),
    priority: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """导出用例为 Excel"""
    filters = {}
    if module:
        filters["module"] = module
    if priority:
        filters["priority"] = priority
    if status:
        filters["status"] = status

    output = await service.export_test_cases_to_excel(db, filters)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=test_cases.xlsx"},
    )


@router.get("/export/test-plan/{plan_id}")
async def export_test_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    """导出测试计划为 Excel"""
    output = await service.export_test_plan_to_excel(db, plan_id)
    if not output:
        raise HTTPException(status_code=404, detail="计划不存在")
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=test_plan_{plan_id}.xlsx"},
    )


@router.post("/import/preview")
async def preview_import(file: UploadFile = File(...)):
    """上传文件并预览解析结果"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in ("xlsx", "xls", "csv"):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx / .xls / .csv 格式")
    result = await service.parse_import_file(file)
    return result


@router.post("/import/confirm")
async def confirm_import(
    data: dict,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    """确认导入：将预览数据写入数据库"""
    rows = data.get("rows", [])
    if not rows:
        raise HTTPException(status_code=400, detail="没有要导入的数据")

    created = 0
    errors = []
    user_id = user.id if user else None
    for i, row in enumerate(rows):
        try:
            case = TestCase(
                user_id=user_id,
                title=row["title"],
                module=row.get("module", "默认模块"),
                priority=PriorityEnum(row.get("priority", "P2")),
                status=CaseStatusEnum.ACTIVE,
                case_type=row.get("case_type", "test"),
                precondition=row.get("precondition", ""),
                steps=row.get("steps", []),
                tags=row.get("tags", []),
                check_category=row.get("check_category"),
                check_criteria=row.get("check_criteria"),
            )
            db.add(case)
            created += 1
        except Exception as e:
            errors.append({"row": i + 2, "message": str(e)})

    await db.commit()
    return {"data": None, "message": f"成功导入 {created} 条用例", "errors": errors}


# ═══════════════════════ 页面路由 ═══════════════════════

@page_router.get("", response_class=HTMLResponse)
async def import_export_page(request: Request):
    """导入导出页面"""
    return templates.TemplateResponse(
        request, "pages/import_export/index.html", {}
    )
