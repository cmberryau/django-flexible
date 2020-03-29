from django.test import TestCase
from django.utils.duration import duration_string
from datetime import timedelta

from flexible.widgets import DurationWidget


class WidgetTests(TestCase):
    def test_duration_widget_decompress(self):
        widget = DurationWidget()

        def test(obj, expected):
            value = duration_string(obj)
            self.assertEqual(widget.decompress(obj), expected)
            self.assertEqual(widget.decompress(value), expected)

        # testing django style timedelta str
        test(timedelta(days=365), [8760, None])
        test(timedelta(days=1, hours=1), [25, None])
        test(timedelta(days=1, minutes=1), [24, 1])
        test(timedelta(days=1, hours=1, minutes=1), [25, 1])
        test(timedelta(days=1, minutes=1, seconds=10), [24, 1])
        test(timedelta(days=1, minutes=0, seconds=120), [24, 2])
        test(timedelta(days=1, minutes=0, seconds=120, microseconds=100), [24, 2])
        test(timedelta(minutes=1), [None, 1])
        test(timedelta(minutes=0), [None, None])
        test(timedelta(minutes=-100), [-2, 20])
        test(timedelta(hours=-10, minutes=1), [-10, 1])
        test(timedelta(), [None, None])
