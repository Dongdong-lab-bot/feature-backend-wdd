from fastapi import Depends, HTTPException, Request
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import UserContext
from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.user.models import User


def _raise(status_code: int, msg: str, code: int) -> None:
    raise HTTPException(status_code=status_code, detail={"code": code, "msg": msg, "data": None})


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    user = getattr(request.state, "user", None)
    if user is not None:
        return user

    UserContext.reset()

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        _raise(401, "unauthorized", 401)

    app_client_header = request.headers.get("X-App-Client")
    if not app_client_header:
        _raise(403, "forbidden", 403)

    token = auth_header.split(" ", 1)[1]
    try:
        claims = decode_access_token(token, app_client_header)
    except (ValueError, InvalidTokenError):
        _raise(401, "unauthorized", 401)

    if claims.get("type") != "access":
        _raise(401, "unauthorized", 401)

    if app_client_header != claims.get("appClient"):
        _raise(403, "forbidden", 403)

    uid = claims.get("uid")
    if uid is None:
        _raise(401, "unauthorized", 401)

    user = await db.get(User, int(uid))
    if not user or user.status != "ACTIVE":
        _raise(403, "forbidden", 403)

    if user.tenant_id != int(claims.get("tenantId", 0)):
        _raise(403, "forbidden", 403)

    if user.token_version != int(claims.get("tokenVersion", 0)):
        _raise(403, "forbidden", 403)

    if claims.get("roleType") != user.role_type:
        _raise(403, "forbidden", 403)

    UserContext.set_user_id(str(user.id))
    UserContext.set_tenant_id(str(user.tenant_id))
    UserContext.set_role_type(user.role_type)
    UserContext.set_app_client(app_client_header)

    request.state.user = user
    return user


async def get_current_user_optional(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:
    """可选认证：有 Token 就返回 User，没有就返回 None。"""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
