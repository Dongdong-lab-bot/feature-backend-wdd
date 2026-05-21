"""Audit logging interface for data_agent.

Aligned with src.core.logger log.audit() contract.
"""

from src.core.logger import log, TraceContext


def audit_log(
    operator: str,
    action: str,
    input_data: str,
    output_data: str,
    success: bool,
    trace_id: str = "",
) -> None:
    """Audit log interface aligned with global audit contract."""
    if not trace_id:
        raise ValueError("audit_log 需要非空 trace_id")

    # 临时设置 trace_id，确保 audit 日志绑定正确的 trace_id
    old_trace_id = TraceContext.get_trace_id()
    TraceContext.set_trace_id(trace_id)
    try:
        log.audit(
            f"[{operator}] {action} | "
            f"input: {input_data} | output: {output_data} | success: {success}"
        )
    finally:
        TraceContext.set_trace_id(old_trace_id)
