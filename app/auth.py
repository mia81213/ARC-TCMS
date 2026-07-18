"""认证模块 — 密码哈希、Token 管理、认证中间件"""

import hashlib
import hmac
import os
import secrets
import time
from typing import Optional

from fastapi import Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User

# 存储活跃 token → user_id 映射（生产环境建议用 Redis）
_active_tokens: dict[str, dict] = {}  # token → {"user_id": int, "expires": float}


def hash_password(password: str) -> str:
    """PBKDF2 密码哈希"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, stored: str) -> bool:
    """验证密码"""
    try:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key, new_key)
    except (ValueError, AttributeError):
        return False


def create_token(user_id: int) -> str:
    """创建 session token，有效期 30 天"""
    token = secrets.token_hex(32)
    _active_tokens[token] = {
        "user_id": user_id,
        "expires": time.time() + 30 * 24 * 3600,  # 30 天
    }
    return token


def verify_token(token: str) -> Optional[int]:
    """验证 token，返回 user_id 或 None"""
    data = _active_tokens.get(token)
    if not data:
        return None
    if time.time() > data["expires"]:
        del _active_tokens[token]
        return None
    return data["user_id"]


def remove_token(token: str):
    """删除 token（登出）"""
    _active_tokens.pop(token, None)


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """FastAPI 依赖：从请求头获取当前用户"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        # 也尝试从 cookie 获取
        token = request.cookies.get("tcms_token", "")

    if not token:
        raise HTTPException(status_code=401, detail="请先登录")

    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    """获取当前用户（可选，不强制登录）"""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
