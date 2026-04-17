from __future__ import annotations

from typing import Any, Dict, List

from app.modules.device.constants import (
    ALERT_TYPE_HIGH_TEMP,
    ALERT_TYPE_NO_MASK,
    TEMPERATURE_ALERT_THRESHOLD,
)
from app.modules.device.exceptions import AlertDispatchError


def build_alert_types(temperature: float, has_mask: bool) -> List[str]:
    alerts: List[str] = []
    if temperature > TEMPERATURE_ALERT_THRESHOLD:
        alerts.append(ALERT_TYPE_HIGH_TEMP)
    if not has_mask:
        alerts.append(ALERT_TYPE_NO_MASK)
    return alerts


async def dispatch_device_alerts(alert_types: List[str], payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        _ = payload
        return {"success": True, "alert_types": alert_types, "error": None}
    except Exception as exc:
        raise AlertDispatchError(str(exc)) from exc
