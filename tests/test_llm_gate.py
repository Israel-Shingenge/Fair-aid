from datetime import datetime, timedelta, timezone as dt_tz
import pytest
from apps.explanations.gate import RateGate

pytestmark = pytest.mark.django_db

CFG = {"MIN_INTERVAL_SECONDS": 12.0, "DAILY_LIMIT": 3, "QUEUE_WAIT_SECONDS": 20.0, "REQUEST_TIMEOUT_SECONDS": 30.0}

class FakeTime:
    def __init__(self):
        self.now = datetime(2026, 10, 17, 12, 0, 0, tzinfo=dt_tz.utc)

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += timedelta(seconds=seconds)

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


@pytest.fixture
def t():
    return FakeTime()

@pytest.fixture
def gate(t):
    return RateGate(CFG, clock=t.clock, sleep=t.sleep)

def test_first_request_goes_straight_through(gate):
    assert gate.acquire().granted

def test_only_one_request_in_flight_second_caller_gives_up_when_wait_too_long(gate):
    first = gate.acquire()
    assert first.granted
    second = gate.acquire()  # first still holds the 32s lease, longer than the 20s wait budget
    assert not second.granted and second.reason == "busy"

def test_next_request_waits_for_min_interval_after_release(gate, t):
    first = gate.acquire()
    t.advance(3)  # the call took 3 seconds
    gate.release(first)
    before = t.now
    second = gate.acquire()
    assert second.granted
    assert (t.now - before).total_seconds() == pytest.approx(9.0, abs=0.2)  # 12s after the first started

def test_slow_call_does_not_add_extra_delay(gate, t):
    first = gate.acquire()
    t.advance(15)
    gate.release(first)
    before = t.now
    assert gate.acquire().granted
    assert (t.now - before).total_seconds() < 0.5

def test_daily_limit_then_resets_on_pacific_midnight(gate, t):
    for _ in range(3):
        permit = gate.acquire()
        assert permit.granted
        gate.release(permit)
        t.advance(13)
    denied = gate.acquire()
    assert not denied.granted and denied.reason == "daily_quota"
    t.advance(24 * 3600)
    assert gate.acquire().granted

def test_429_blocks_gate_for_retry_delay(gate, t):
    permit = gate.acquire()
    gate.block(seconds=40, daily=False)
    gate.release(permit)
    denied = gate.acquire()  # 41s block > 20s wait budget
    assert not denied.granted and denied.reason == "rate_limited"
    t.advance(45)
    assert gate.acquire().granted

def test_daily_429_blocks_until_reset(gate, t):
    permit = gate.acquire()
    gate.block(seconds=None, daily=True)
    gate.release(permit)
    assert gate.acquire().reason == "daily_quota"
    assert gate.status()["requests_remaining_today"] == 0

def test_refund_returns_the_slot(gate):
    permit = gate.acquire()
    gate.release(permit, refund=True)
    assert gate.status()["requests_today"] == 0
