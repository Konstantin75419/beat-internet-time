"""Core conversion logic for Swatch Internet Time (".beats").

Terminology
-----------
* **beat** — one thousandth of a day, exactly 86.4 seconds.
* **seconds_into_day** — the number of seconds since UTC midnight,
  in the range [0, SECONDS_PER_DAY).

The central invariant is that beats are always a non-negative integer in
the range [0, 999]; fractional beats are not produced by this library.
Rounding is done with Python's built-in round() (banker's rounding),
which halves to the nearest even value. This is documented here so
callers know exactly what to expect on a boundary input.
"""

from __future__ import annotations

import time as _time
from datetime import datetime, timedelta
from typing import Union

BEATS_PER_DAY = 1000
SECONDS_PER_DAY = 86_400
SECONDS_PER_BEAT = 86.4  # 86_400 / 1000; exact in binary floating point? No, but fine.


Number = Union[int, float]


class BeatTime:
    """A point in time expressed in .beats.

    We keep the *integer* beat count as the canonical value. A
    corresponding seconds-since-UTC-midnight value is derived from it so
    callers can easily obtain a standard timestamp.

    The object is intentionally immutable and hashable: two BeatTime
    values are equal iff their beat counts are equal.
    """

    __slots__ = ("_beats",)

    def __init__(self, beats: int) -> None:
        if not isinstance(beats, int):
            raise TypeError(f"beats must be int, not {type(beats).__name__}")
        if beats < 0 or beats >= BEATS_PER_DAY:
            raise ValueError(f"beats must be in [0, {BEATS_PER_DAY}), got {beats}")
        self._beats = beats

    @property
    def beats(self) -> int:
        return self._beats

    @property
    def seconds_into_day(self) -> float:
        """Seconds since UTC midnight corresponding to this beat."""
        return self._beats * SECONDS_PER_BEAT

    @property
    def datetime(self) -> datetime:
        """A naive UTC datetime for today's date at this beat.

        The date component is the current UTC date; the time component is
        derived from the beat count.
        """
        today = datetime.utcnow().date()
        secs = self._beats * SECONDS_PER_BEAT
        return datetime.combine(today, datetime.min.time()) + timedelta(seconds=secs)

    def __int__(self) -> int:
        return self._beats

    def __float__(self) -> float:
        return self._beats * SECONDS_PER_BEAT

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BeatTime):
            return self._beats == other._beats
        return NotImplemented

    def __lt__(self, other: "BeatTime") -> bool:
        if not isinstance(other, BeatTime):
            return NotImplemented
        return self._beats < other._beats

    def __le__(self, other: "BeatTime") -> bool:
        if not isinstance(other, BeatTime):
            return NotImplemented
        return self._beats <= other._beats

    def __gt__(self, other: "BeatTime") -> bool:
        if not isinstance(other, BeatTime):
            return NotImplemented
        return self._beats > other._beats

    def __ge__(self, other: "BeatTime") -> bool:
        if not isinstance(other, BeatTime):
            return NotImplemented
        return self._beats >= other._beats

    def __hash__(self) -> int:
        return hash(("BeatTime", self._beats))

    def __repr__(self) -> str:
        return f"BeatTime(beats={self._beats})"

    def __str__(self) -> str:
        return f"@{self._beats:03d}"

    def __format__(self, fmt: str) -> str:
        """Format the beat string.

        With no format spec or an empty spec, returns the standard
        '@NNN' string. If an integer precision ``.Nd`` is given (e.g.
        ``{:.3d}``), the digits after '@' are zero-padded to that width.
        This mirrors how datetime formatting is approached: a small,
        predictable surface.
        """
        if fmt == "":
            return str(self)
        # Accept specs like "03d", "3d", etc.
        cleaned = fmt
        if cleaned.endswith("d"):
            cleaned = cleaned[:-1]
        try:
            width = int(cleaned) if cleaned else 3
        except ValueError as exc:
            raise ValueError(f"Unknown format specifier {fmt!r} for BeatTime") from exc
        return f"@{self._beats:0{width}d}"


def to_beats(seconds_into_day: Number) -> int:
    """Convert seconds-since-UTC-midnight to a beat count in [0, 999].

    Uses round() (banker's rounding). An input of exactly 86_400 seconds
    is treated as @999, because the day has no @1000; this mirrors how
    the 24:00:00 instant is conventionally the same as 00:00:00 of the
    *next* day, but here we clamp rather than roll, so callers who pass
    a slightly-over value (e.g. 86400.0 from float imprecision) don't
    get an out-of-range result.
    """
    if not isinstance(seconds_into_day, (int, float)):
        raise TypeError(
            f"seconds_into_day must be int or float, not {type(seconds_into_day).__name__}"
        )
    if seconds_into_day < 0:
        raise ValueError(
            f"seconds_into_day must be non-negative, got {seconds_into_day}"
        )
    if seconds_into_day >= SECONDS_PER_DAY:
        return BEATS_PER_DAY - 1
    beats = round(seconds_into_day / SECONDS_PER_BEAT)
    if beats >= BEATS_PER_DAY:
        return BEATS_PER_DAY - 1
    return int(beats)


def to_seconds(beats: int) -> float:
    """Convert a beat count to seconds-since-UTC-midnight.

    ``beats`` must be an integer in [0, 999]. The returned value is a
    float because one beat is 86.4 seconds, which is not an integer.
    """
    if not isinstance(beats, int):
        raise TypeError(f"beats must be int, not {type(beats).__name__}")
    if beats < 0 or beats >= BEATS_PER_DAY:
        raise ValueError(f"beats must be in [0, {BEATS_PER_DAY}), got {beats}")
    return beats * SECONDS_PER_BEAT


def now(clock=_time.time) -> BeatTime:
    """Return the current BeatTime.

    ``clock`` is a callable returning seconds since the Unix epoch, like
    :func:`time.time`. It is injectable so tests can pass a deterministic
    fake clock — we never read the wall clock directly in a way that
    would make tests flaky.

    The epoch seconds are converted to a UTC time-of-day, then to beats.
    Because we use UTC, every caller everywhere sees the same beat value,
    which is the entire purpose of Internet Time.
    """
    epoch = float(clock())
    # datetime.utcfromtimestamp is the stdlib way to get naive UTC from epoch.
    dt = datetime.utcfromtimestamp(epoch)
    seconds_into_day = dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
    return BeatTime(to_beats(seconds_into_day))
