from __future__ import annotations

import json
from uuid import uuid4

from jwt import InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.context import UserContext
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.modules.user.models import User as UserModel


def _error(status_code: int, msg: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"code": status_code, "msg": msg, "data": None})


def _attach_request_id(response: Response, request_id: str) -> Response:
    response.headers["X-Request-Id"] = request_id
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response
    body = getattr(response, "body", None)
    if not body:
        return response
    try:
        payload = json.loads(body)
    except Exception:
        return response
    if isinstance(payload, dict) and "request_id" not in payload:
        payload["request_id"] = request_id
        response.body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        response.headers["content-length"] = str(len(response.body))
    return response


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        UserContext.reset()

        request_id = request.headers.get("X-Request-Id") or uuid4().hex
        request.state.request_id = request_id

        path = request.url.path
        if (
            path == "/"
            or path == "/health"
            or path.startswith("/docs")
            or path == "/openapi.json"
            or path.startswith("/auth/login")
            or path.startswith("/auth/refresh")
            or path.startswith("/auth/sms/")
            or path.startswith("/auth/register")
            or path.startswith("/auth/password/")
            or path.startswith("/auth/idp/")
            or path.startswith("/api/v1/auth/")
            or path.startswith("/tenant")
            or path.startswith("/image_license")
            or path.startswith("/files/public/")
        ):
            response = await call_next(request)
            return _attach_request_id(response, request_id)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return _attach_request_id(_error(401, "unauthorized"), request_id)

        app_client = request.headers.get("X-App-Client")
        if not app_client:
            return _attach_request_id(_error(403, "forbidden"), request_id)

        token = auth_header.split(" ", 1)[1]
        try:
            claims = decode_access_token(token, app_client)
        except (ValueError, InvalidTokenError):
            return _attach_request_id(_error(401, "unauthorized"), request_id)

        if claims.get("type") != "access":
            return _attach_request_id(_error(401, "unauthorized"), request_id)

        if app_client != claims.get("appClient"):
            return _attach_request_id(_error(403, "forbidden"), request_id)

        uid = claims.get("uid")
        tenant_id = claims.get("tenantId")
        if uid is None or tenant_id is None:
            return _attach_request_id(_error(401, "unauthorized"), request_id)

        UserContext.set_user_id(str(uid))
        UserContext.set_tenant_id(str(tenant_id))
        UserContext.set_role_type(str(claims.get("roleType") or ""))
        UserContext.set_app_client(app_client)

        async with SessionLocal() as db:
            user = await db.get(UserModel, int(uid))
            if not user or user.status != "ACTIVE":
                UserContext.reset()
                return _attach_request_id(_error(403, "forbidden"), request_id)

            if user.tenant_id != int(tenant_id):
                UserContext.reset()
                return _attach_request_id(_error(403, "forbidden"), request_id)

            if user.token_version != int(claims.get("tokenVersion", 0)):
                UserContext.reset()
                return _attach_request_id(_error(403, "forbidden"), request_id)

            if str(claims.get("roleType")) != user.role_type:
                UserContext.reset()
                return _attach_request_id(_error(403, "forbidden"), request_id)

            request.state.user = user

        try:
            response = await call_next(request)
            return _attach_request_id(response, request_id)
        finally:
            UserContext.reset()


__all__ = ["AuthMiddleware"]
