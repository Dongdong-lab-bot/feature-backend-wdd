from __future__ import annotations

from typing import Any, Dict, Optional

from app.modules.device.exceptions import LedgerBackfillError


async def backfill_morning_check_ledger(payload: Dict[str, Any]) -> Dict[str, Optional[str] | bool]:
    try:
        _ = payload
        return {"success": True, "ledger_id": None, "error": None}
    except Exception as exc:
        raise LedgerBackfillError(str(exc)) from exc
