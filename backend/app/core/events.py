"""Lightweight event definitions and dispatch helpers."""

from datetime import datetime
import logging
from typing import Any, Dict

from fastapi_events.dispatcher import dispatch

logger = logging.getLogger(__name__)

# Event names
TENANT_CREATED = "tenant.created"


def publish(event_name: str, payload: Dict[str, Any]) -> None:
    """Publish an event via fastapi-events dispatcher; degrade gracefully when middleware is absent (e.g., tests)."""
    logger.info("event %s payload=%s", event_name, payload)
    try:
        dispatch(event_name, payload)
    except LookupError:
        logger.info("event dispatch skipped (no middleware context)")


def emit_tenant_created(*, tenant_id: str, admin_user_id: str, created_at: datetime) -> None:
    """Helper to publish tenant.created with required payload."""
    payload = {
        "tenant_id": tenant_id,
        "admin_user_id": admin_user_id,
        "created_at": created_at.isoformat(),
    }
    publish(TENANT_CREATED, payload)
