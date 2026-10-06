"""Beat Internet Time.

A small library for converting between standard time and Swatch Internet
Time (".beats"). The day is divided into 1000 beats of exactly 86.4
seconds each. A day runs from @000 to @999.

Design decision: we work with *naive* UTC throughout. The original Swatch
Internet Time deliberately avoided time zones — the whole point was to
give every place on Earth the same beat count at the same instant. So we
use UTC as the single, universal reference and never introduce tzinfo.
This keeps the API tiny and avoids the semantic morass of DST and zone
naming.
"""

from .core import (
    BEATS_PER_DAY,
    SECONDS_PER_DAY,
    SECONDS_PER_BEAT,
    BeatTime,
    to_beats,
    to_seconds,
    now,
)

__all__ = [
    "BEATS_PER_DAY",
    "SECONDS_PER_DAY",
    "SECONDS_PER_BEAT",
    "BeatTime",
    "to_beats",
    "to_seconds",
    "now",
]
