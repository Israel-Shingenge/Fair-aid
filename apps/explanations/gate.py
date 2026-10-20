"""
Serialises access to the LLM so the free tier is never exceeded, across every web worker process.

Guarantees:
  * at most ONE request in flight (a lease is held from acquire() to release());
  * at least ``MIN_INTERVAL_SECONDS`` between request starts (per-minute limit);
  * at most ``DAILY_LIMIT`` requests per Pacific-time day (per-day limit);
  * after a 429 the gate stays closed for the provider's ``retryDelay`` (or until the daily reset).

Callers wait at most ``QUEUE_WAIT_SECONDS`` for a slot; beyond that they get a denial and fall back to
the deterministic explanation instead of hanging. Slots are taken with a conditional UPDATE, which is
atomic on both SQLite and PostgreSQL, so no explicit locking or Redis is needed.
"""
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional
from zoneinfo import ZoneInfo

from django.db.models import F
from django.utils import timezone

from .llm import LOCAL_NO_LIMIT, gate_config
from .models import LLMGate

PACIFIC = ZoneInfo("America/Los_Angeles")

@dataclass(frozen=True)
class Permit:
    granted: bool
    reason: Optional[str] = None  # when denied: "busy" | "rate_limited" | "daily_quota"
    started_at: Optional[datetime] = None

class RateGate:
    def __init__(
        self,
        cfg: Optional[dict] = None,
        clock: Callable[[], datetime] = timezone.now,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.cfg = cfg or gate_config()
        self.clock = clock
        self.sleep = sleep

    # -- helpers --
    def _today(self, now: datetime):
        return now.astimezone(PACIFIC).date()

    def _next_reset(self, now: datetime) -> datetime:
        local = now.astimezone(PACIFIC)
        midnight = datetime.combine(local.date() + timedelta(days=1), datetime.min.time(), tzinfo=PACIFIC)
        return midnight.astimezone(now.tzinfo)

    def _lease_seconds(self) -> float:
        return self.cfg["REQUEST_TIMEOUT_SECONDS"] + 2  # a crashed worker's lease expires on its own

    def _ensure_row(self, now: datetime) -> None:
        LLMGate.objects.get_or_create(pk=1, defaults={"next_slot_at": now - timedelta(seconds=1)})
        LLMGate.objects.filter(pk=1).exclude(window_date=self._today(now)).update(
            window_date=self._today(now), requests_today=0
        )

    # -- API --
    def acquire(self) -> Permit:
        start = self.clock()
        deadline = start + timedelta(seconds=self.cfg["QUEUE_WAIT_SECONDS"])
        limit = self.cfg["DAILY_LIMIT"]
        self._ensure_row(start)

        while True:
            now = self.clock()
            self._ensure_row(now)
            gate = LLMGate.objects.get(pk=1)

            if gate.requests_today >= limit:
                return Permit(False, "daily_quota")
            if gate.blocked_until and gate.blocked_until > now:
                if gate.block_reason == "daily_quota" or gate.blocked_until > deadline:
                    return Permit(False, gate.block_reason or "rate_limited")
                self.sleep((gate.blocked_until - now).total_seconds())
                continue
            if gate.next_slot_at > now:
                if gate.next_slot_at > deadline:
                    return Permit(False, "busy")
                self.sleep(max((gate.next_slot_at - now).total_seconds(), 0.05))
                continue

            taken = LLMGate.objects.filter(pk=1, next_slot_at__lte=now, requests_today__lt=limit).update(
                next_slot_at=now + timedelta(seconds=self._lease_seconds()),
                requests_today=F("requests_today") + 1,
                blocked_until=None,
                block_reason="",
            )
            if taken:
                return Permit(True, started_at=now)
            self.sleep(0.05)  # lost the race to another worker; look again

    def release(self, permit: Permit, refund: bool = False) -> None:
        """Free the lease. The next request may start MIN_INTERVAL after this one started."""
        if not permit.granted:
            return
        now = self.clock()
        if refund:  # the slot wasn't actually used (e.g. answer found in cache after waiting)
            LLMGate.objects.filter(pk=1, requests_today__gt=0).update(
                next_slot_at=now, requests_today=F("requests_today") - 1
            )
            return
        earliest = permit.started_at + timedelta(seconds=self.cfg["MIN_INTERVAL_SECONDS"])
        LLMGate.objects.filter(pk=1).update(next_slot_at=max(now, earliest))

    def block(self, seconds: Optional[float], daily: bool) -> None:
        """Record a 429 from the provider."""
        now = self.clock()
        if daily:
            LLMGate.objects.filter(pk=1).update(
                blocked_until=self._next_reset(now), block_reason="daily_quota",
                requests_today=self.cfg["DAILY_LIMIT"],
            )
        else:
            wait = seconds if seconds is not None else 60.0
            LLMGate.objects.filter(pk=1).update(
                blocked_until=now + timedelta(seconds=wait + 1), block_reason="rate_limited"
            )

    def status(self) -> Dict:
        now = self.clock()
        self._ensure_row(now)
        gate = LLMGate.objects.get(pk=1)
        unlimited = self.cfg["DAILY_LIMIT"] >= LOCAL_NO_LIMIT
        return {
            "requests_today": gate.requests_today,
            "daily_limit": None if unlimited else self.cfg["DAILY_LIMIT"],
            "requests_remaining_today": None if unlimited else max(self.cfg["DAILY_LIMIT"] - gate.requests_today, 0),
            "next_slot_at": gate.next_slot_at,
            "blocked_until": gate.blocked_until if gate.blocked_until and gate.blocked_until > now else None,
            "block_reason": gate.block_reason or None,
            "window": "Pacific-time day",
        }
