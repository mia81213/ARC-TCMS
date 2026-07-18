"""认证路由"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password, verify_password, create_token, remove_token, get_current_user
from app.database import get_db
from app.models.user import User
from app.templates import templates

router = APIRouter(prefix="/api/auth", tags=["auth"])
page_router = APIRouter(prefix="/app", tags=["pages-auth"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """注册新用户"""
    # 检查用户名是否已被占用
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名已被注册")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_token(user.id)
    return {"data": {"id": user.id, "username": user.username, "token": token}}


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """登录"""
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_token(user.id)
    return {"data": {"id": user.id, "username": user.username, "token": token}}


@router.post("/logout")
async def logout(request: Request):
    """登出"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        token = request.cookies.get("tcms_token", "")
    if token:
        remove_token(token)
    return {"data": None, "message": "已登出"}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {"data": {"id": user.id, "username": user.username}}


# ═══════════════════════ 页面 ═══════════════════════

@page_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录页"""
    return templates.TemplateResponse(request, "pages/auth/login.html", {})


@page_router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """注册页"""
    return templates.TemplateResponse(request, "pages/auth/register.html", {})
