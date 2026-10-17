"""
Reviewer Clock Override System
Stores timestamps in UTC, provides timezone conversions to IST (Asia/Kolkata),
and supports X-Test-Clock headers or programmatic overrides for testing time-dependent rules.
"""

from contextvars import ContextVar
from datetime import datetime, date, timezone, timedelta
from typing import Optional
from dateutil import parser

try:
    from zoneinfo import ZoneInfo
    try:
        IST = ZoneInfo("Asia/Kolkata")
    except Exception:
        IST = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")
except ImportError:
    IST = timezone(timedelta(hours=5, minutes=30), name="Asia/Kolkata")

UTC = timezone.utc

# Context variable for per-request test clock override
_request_test_clock: ContextVar[Optional[datetime]] = ContextVar("request_test_clock", default=None)
# Global override fallback for tests or admin setting
_global_test_clock: Optional[datetime] = None


def set_request_clock(override: Optional[datetime]) -> None:
    """Set the test clock for the current request context."""
    if override and override.tzinfo is None:
        override = override.replace(tzinfo=UTC)
    elif override:
        override = override.astimezone(UTC)
    _request_test_clock.set(override)


def set_global_clock(override: Optional[datetime]) -> None:
    """Set global test clock (primarily for integration tests / seed scripts)."""
    global _global_test_clock
    if override and override.tzinfo is None:
        override = override.replace(tzinfo=UTC)
    elif override:
        override = override.astimezone(UTC)
    _global_test_clock = override


def parse_clock_string(value: str) -> datetime:
    """Parse a date or ISO timestamp string into a UTC datetime."""
    dt = parser.parse(value)
    if dt.tzinfo is None:
        # Default to UTC if not specified
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt


def get_current_time() -> datetime:
    """Returns the current effective UTC datetime (override or system clock)."""
    req = _request_test_clock.get()
    if req is not None:
        return req
    if _global_test_clock is not None:
        return _global_test_clock
    return datetime.now(UTC)


def get_current_date() -> date:
    """Returns the current effective UTC date (or IST date if evaluated in IST)."""
    return get_current_time().date()


def to_ist(dt: datetime) -> datetime:
    """Convert a UTC datetime to IST (Asia/Kolkata)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(IST)


def format_ist(dt: Optional[datetime]) -> Optional[str]:
    """Format UTC datetime as readable IST ISO string."""
    if dt is None:
        return None
    ist_dt = to_ist(dt)
    return ist_dt.strftime("%Y-%m-%d %H:%M:%S IST")
