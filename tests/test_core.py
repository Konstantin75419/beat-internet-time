import unittest
from datetime import datetime

from beat_internet_time.core import (
    BEATS_PER_DAY,
    SECONDS_PER_BEAT,
    SECONDS_PER_DAY,
    BeatTime,
    to_beats,
    to_seconds,
    now,
)


class TestConstants(unittest.TestCase):
    def test_beats_per_day(self):
        self.assertEqual(BEATS_PER_DAY, 1000)

    def test_seconds_per_day(self):
        self.assertEqual(SECONDS_PER_DAY, 86400)

    def test_seconds_per_beat(self):
        self.assertAlmostEqual(SECONDS_PER_BEAT, 86.4)


class TestToBeats(unittest.TestCase):
    def test_midnight(self):
        self.assertEqual(to_beats(0), 0)

    def test_one_beat(self):
        self.assertEqual(to_beats(86.4), 1)

    def test_last_beat_boundary(self):
        # The start of the last beat (999 * 86.4) should map to @999.
        self.assertEqual(to_beats(999 * 86.4), 999)

    def test_at_exactly_one_day(self):
        # 86400 is the end of the day; there is no @1000, so we clamp.
        self.assertEqual(to_beats(86400), 999)

    def test_beyond_one_day_clamps(self):
        # Defensive: if a caller passes 86400 + 1, we still return @999
        # rather than raising. This is the clamp behaviour documented in
        # the docstring.
        self.assertEqual(to_beats(86401), 999)

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            to_beats(-1)

    def test_non_number_raises(self):
        with self.assertRaises(TypeError):
            to_beats("100")  # type: ignore[arg-type]


class TestToSeconds(unittest.TestCase):
    def test_zero_beats(self):
        self.assertEqual(to_seconds(0), 0.0)

    def test_one_beat(self):
        self.assertAlmostEqual(to_seconds(1), 86.4)

    def test_max_beats(self):
        self.assertAlmostEqual(to_seconds(999), 999 * 86.4)

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            to_seconds(-1)

    def test_too_high_raises(self):
        with self.assertRaises(ValueError):
            to_seconds(1000)

    def test_non_int_raises(self):
        with self.assertRaises(TypeError):
            to_seconds(1.0)  # type: ignore[arg-type]


class TestRoundTrip(unittest.TestCase):
    def test_round_trip_all_beats(self):
        for b in range(BEATS_PER_DAY):
            secs = to_seconds(b)
            # Because beats are discrete and seconds are continuous,
            # going beats -> seconds -> beats must be identity.
            self.assertEqual(to_beats(secs), b)


class TestBeatTime(unittest.TestCase):
    def test_valid_beats(self):
        bt = BeatTime(500)
        self.assertEqual(bt.beats, 500)
        self.assertEqual(int(bt), 500)

    def test_invalid_beats_high(self):
        with self.assertRaises(ValueError):
            BeatTime(1000)

    def test_invalid_beats_negative(self):
        with self.assertRaises(ValueError):
            BeatTime(-1)

    def test_non_int_beats(self):
        with self.assertRaises(TypeError):
            BeatTime(1.0)  # type: ignore[arg-type]

    def test_str(self):
        self.assertEqual(str(BeatTime(0)), "@000")
        self.assertEqual(str(BeatTime(42)), "@042")
        self.assertEqual(str(BeatTime(999)), "@999")

    def test_repr(self):
        self.assertEqual(repr(BeatTime(42)), "BeatTime(beats=42)")

    def test_equality(self):
        self.assertEqual(BeatTime(123), BeatTime(123))
        self.assertNotEqual(BeatTime(123), BeatTime(124))

    def test_equality_with_other_type(self):
        # Not equal to a plain int, even with the same value.
        self.assertNotEqual(BeatTime(5), 5)

    def test_hashable(self):
        bt1 = BeatTime(10)
        bt2 = BeatTime(10)
        bt3 = BeatTime(20)
        self.assertEqual(hash(bt1), hash(bt2))
        self.assertNotEqual(hash(bt1), hash(bt3))
        # Usable as a dict key / set member.
        self.assertIn(bt1, {bt1, bt3})

    def test_ordering(self):
        a = BeatTime(100)
        b = BeatTime(200)
        self.assertTrue(a < b)
        self.assertTrue(a <= b)
        self.assertTrue(b > a)
        self.assertTrue(b >= a)
        self.assertFalse(a == b)

    def test_seconds_into_day(self):
        bt = BeatTime(1)
        self.assertAlmostEqual(bt.seconds_into_day, 86.4)

    def test_float_conversion(self):
        self.assertAlmostEqual(float(BeatTime(2)), 172.8)

    def test_format_default(self):
        self.assertEqual(f"{BeatTime(7)}", "@007")

    def test_format_with_width(self):
        self.assertEqual(f"{BeatTime(7):05d}", "@00007")


class TestNow(unittest.TestCase):
    """now() takes an injectable clock so tests are deterministic."""

    def test_midnight_utc(self):
        # 2000-01-01 00:00:00 UTC is epoch 946684800.
        clock = lambda: 946684800
        bt = now(clock)
        self.assertEqual(bt.beats, 0)

    def test_one_beat_after_midnight(self):
        # 86.4 seconds after midnight UTC -> @001.
        clock = lambda: 946684800 + 86.4
        bt = now(clock)
        self.assertEqual(bt.beats, 1)

    def test_noon_utc(self):
        # 12:00:00 UTC = 43200 seconds into the day -> beat 500.
        clock = lambda: 946684800 + 43200
        bt = now(clock)
        self.assertEqual(bt.beats, 500)

    def test_last_second_of_day(self):
        # 23:59:59 UTC = 86399 seconds into day. That's in beat 999.
        clock = lambda: 946684800 + 86399
        bt = now(clock)
        self.assertEqual(bt.beats, 999)


if __name__ == "__main__":
    unittest.main()
