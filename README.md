# Beat Internet Time

Converts between standard time and Swatch Internet Time (.beats), where a day is divided into 1000 beats of 86.4 seconds each, running from @000 to @999.

## Usage

```python
from beat_internet_time import to_beats, to_seconds, now, BeatTime

# Seconds since UTC midnight -> beat count (int in [0, 999]).
beat = to_beats(43200)      # noon UTC -> 500

# Beat count -> seconds since UTC midnight (float, one beat = 86.4s).
secs = to_seconds(500)      # -> 43200.0

# A small value object with ordering, str, and formatting.
bt = BeatTime(beat)
print(bt)                   # @500
print(f"{bt:05d}")         # @00500

# Current beat, with an injectable clock for deterministic tests.
current = now()            # BeatTime, uses time.time by default
fake = now(lambda: 946684800 + 43200)  # -> BeatTime(500)
```

## Why this exists

Internet Time was introduced by Swatch in the late 1990s as a time zone–free way to express the same instant everywhere on Earth. This library gives a tiny, dependency-free way to convert between seconds and beats without pulling in a date library or thinking about zones.

The trade-off is that we work in *naive UTC* only. The original scheme deliberately ignored time zones, so we do too: every caller, everywhere, gets the same beat value for the same instant. If you need to convert a local wall-clock time, first shift it to UTC yourself, then call `to_beats`. We do not attempt zone naming or DST handling.

## The awkward edge

A day has exactly 86400 seconds and 1000 beats, so each beat is 86.4 seconds — not an integer. Because beats are reported as integers, inputs that fall on a beat boundary round using Python's banker's rounding (round-half-to-even). An input of exactly 86400 seconds (end of day) is clamped to @999 rather than rolling to @000, so a slightly-over value from float imprecision does not produce an out-of-range or wrapped result.

## Exported names

`BEATS_PER_DAY`, `SECONDS_PER_DAY`, `SECONDS_PER_BEAT`, `BeatTime`, `to_beats`, `to_seconds`, `now`.
