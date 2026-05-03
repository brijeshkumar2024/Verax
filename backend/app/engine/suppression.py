from __future__ import annotations

from datetime import datetime


def build_suppression_key(merchant_id: str, trigger_type: str, timestamp_utc: str, strategy: str = "") -> str:
    dt = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
    slot = f"{dt.year}{dt.month:02d}{dt.day:02d}{dt.hour:02d}"
    return f"{merchant_id}:{trigger_type}:{strategy or 'none'}:{slot}"
