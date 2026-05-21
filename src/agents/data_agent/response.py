"""Standard response builder for DataAgent and tool outputs."""

from typing import Any

from src.core.exceptions import ErrorCodeEnum


def standard_response(
    error_code: ErrorCodeEnum,
    data: Any = None,
    message: str = "",
    trace_id: str = "",
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build unified response payload aligned with architecture contract."""
    return {
        "code": error_code.value,
        "data": data,
        "message": message,
        "detail": detail or {},
        "trace_id": trace_id,
        "success": error_code == ErrorCodeEnum.SUCCESS,
    }
