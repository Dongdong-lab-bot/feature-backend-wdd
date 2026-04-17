import logging
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, DataError

from app.modules.ledger.exceptions import FieldValidationError
from app.modules.inspection.exceptions import InvalidStateTransitionError
from app.db.tenant_interceptor import TenantAccessError
from app.db.security_guard import SecurityException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "msg": str(exc.detail), "data": None},
        )

    @app.exception_handler(FieldValidationError)
    async def field_validation_error_handler(request: Request, exc: FieldValidationError):
        return JSONResponse(
            status_code=400,
            content={
                "code": 40001,
                "msg": "表单字段校验失败",
                "data": {"field_id": exc.field_id, "detail": exc.message},
            },
        )

    @app.exception_handler(InvalidStateTransitionError)
    async def invalid_state_transition_handler(request: Request, exc: InvalidStateTransitionError):
        return JSONResponse(
            status_code=400,
            content=exc.to_dict()
        )

    @app.exception_handler(TenantAccessError)
    async def tenant_access_error_handler(request: Request, exc: TenantAccessError):
        logger.warning(f"Tenant access error: {exc}")
        return JSONResponse(
            status_code=403,
            content={
                "code": 40301,
                "msg": "无权访问其他租户的数据",
                "data": None
            },
        )

    @app.exception_handler(SecurityException)
    async def security_exception_handler(request: Request, exc: SecurityException):
        logger.error(f"Security block: {exc}")
        return JSONResponse(
            status_code=403,
            content={
                "code": 40302,
                "msg": "安全拦截：操作被拒绝",
                "data": None
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.error(f"Integrity error: {exc}")

        error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)

        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            msg = "数据已存在，请检查唯一约束字段"
        elif "foreign key" in error_msg.lower():
            msg = "关联的数据不存在，请检查外键字段"
        else:
            msg = "数据完整性约束冲突"

        return JSONResponse(
            status_code=400,
            content={
                "code": 40002,
                "msg": msg,
                "data": {"detail": error_msg}
            },
        )

    @app.exception_handler(DataError)
    async def data_error_handler(request: Request, exc: DataError):
        logger.error(f"Data error: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "code": 40003,
                "msg": "数据格式错误",
                "data": {"detail": str(exc)}
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Unhandled exception: {type(exc).__name__}: {exc}",
            exc_info=True
        )

        is_prod = os.getenv("ENVIRONMENT", "development") == "production"

        if is_prod:
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "msg": "服务器内部错误",
                    "data": None
                },
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "code": 500,
                    "msg": f"服务器内部错误: {type(exc).__name__}",
                    "data": {
                        "detail": str(exc),
                        "type": type(exc).__name__
                    }
                },
            )
