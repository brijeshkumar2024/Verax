from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Deque, Dict, List, Optional

from app.config import DETERMINISTIC_MODE


@dataclass
class Interaction:
    timestamp: datetime
    trigger: str
    cta: str
    message: str
    customer_id: Optional[str] = None
    message_type: str = "info"
    cta_type: str = "explore"
    response: str = "ignored"


@dataclass
class MerchantMemory:
    key_values: Dict[str, str] = field(default_factory=dict)
    interactions: Deque[Interaction] = field(default_factory=lambda: deque(maxlen=200))
    last_message_type: str = "info"
    last_cta_type: str = "explore"
    last_response: str = "ignored"
    last_sent_at: Optional[datetime] = None


class InMemoryState:
    def __init__(self) -> None:
        self._merchant_state: Dict[str, MerchantMemory] = defaultdict(MerchantMemory)
        self._suppression_windows: Dict[str, datetime] = {}
        self._lock = Lock()

    def set_context(self, merchant_id: str, data: Dict[str, str]) -> None:
        with self._lock:
            self._merchant_state[merchant_id].key_values.update(data)

    def get_context(self, merchant_id: str) -> Dict[str, str]:
        with self._lock:
            return dict(self._merchant_state[merchant_id].key_values)

    def add_interaction(
        self,
        merchant_id: str,
        trigger: str,
        cta: str,
        message: str,
        customer_id: Optional[str] = None,
        message_type: str = "info",
        cta_type: str = "explore",
        response: str = "ignored",
    ) -> None:
        if DETERMINISTIC_MODE:
            return
        with self._lock:
            now = datetime.now(timezone.utc)
            memory = self._merchant_state[merchant_id]
            memory.interactions.append(
                Interaction(
                    timestamp=now,
                    trigger=trigger,
                    cta=cta,
                    message=message,
                    customer_id=customer_id,
                    message_type=message_type,
                    cta_type=cta_type,
                    response=response,
                )
            )
            memory.last_message_type = message_type
            memory.last_cta_type = cta_type
            memory.last_response = response
            memory.last_sent_at = now

    def get_recent_interactions(self, merchant_id: str, minutes: int = 1440) -> List[Interaction]:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        with self._lock:
            return [i for i in self._merchant_state[merchant_id].interactions if i.timestamp >= cutoff]

    def get_memory_signals(self, merchant_id: str) -> Dict[str, str]:
        with self._lock:
            memory = self._merchant_state[merchant_id]
            return {
                "last_message_type": memory.last_message_type,
                "last_cta_type": memory.last_cta_type,
                "last_response": memory.last_response,
                "last_sent_at": memory.last_sent_at.isoformat() if memory.last_sent_at else "",
            }

    def set_last_response(self, merchant_id: str, response: str) -> None:
        with self._lock:
            self._merchant_state[merchant_id].last_response = response

    def is_suppressed(self, suppression_key: str, window_minutes: int) -> bool:
        if DETERMINISTIC_MODE:
            return False
        now = datetime.now(timezone.utc)
        with self._lock:
            until = self._suppression_windows.get(suppression_key)
            if until and until > now:
                return True
            self._suppression_windows[suppression_key] = now + timedelta(minutes=window_minutes)
            return False


state = InMemoryState()
