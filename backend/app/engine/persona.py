from __future__ import annotations

from app.engine.types import FusedSignals


def route_persona(fused: FusedSignals, trigger_type: str, customer_id: str | None) -> str:
    if trigger_type in {"rating_dip", "inventory_expiry"}:
        return "system"
    if customer_id is not None:
        return "merchant"
    return "vera"
