"""Ledger module security helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Dict


def calculate_security_hash(content: Dict, snapshot: Dict, salt: str) -> str:
    """Combine content + schema snapshot + salt to produce deterministic sha256 hash."""

    raw = json.dumps(content, sort_keys=True, separators=(",", ":"))
    raw += json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    raw += salt
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
