import importlib
import sys
import unittest
from types import SimpleNamespace


class _FakeQ:
    def __init__(self, *args, **kwargs):
        pass

    def __and__(self, other):
        return self


class _FakeField:
    def __init__(self, *args, **kwargs):
        pass


class _FakeDocument:
    pass


sys.modules.setdefault(
    'mongoengine',
    SimpleNamespace(
        Q=_FakeQ,
        connect=lambda *args, **kwargs: None,
        Document=_FakeDocument,
        StringField=_FakeField,
        DateTimeField=_FakeField,
        IntField=_FakeField,
        FloatField=_FakeField,
        BooleanField=_FakeField,
    ),
)
sys.modules.setdefault(
    'pandas',
    SimpleNamespace(
        DataFrame=type('DataFrame', (), {}),
    ),
)
sys.modules.setdefault(
    'config',
    SimpleNamespace(
        mongodb_config={'db': 'test'},
    ),
)
sys.modules.setdefault(
    'logger',
    SimpleNamespace(
        setup_logging=lambda *args, **kwargs: None,
    ),
)
sys.modules.setdefault(
    'models',
    SimpleNamespace(
        QuantResult=type('QuantResult', (), {}),
        StockDailyTrading=type('StockDailyTrading', (), {}),
    ),
)
sys.modules.setdefault(
    'analysis.technical_analysis_util',
    SimpleNamespace(
        calculate_ma=lambda *args, **kwargs: None,
        check_duplicate_strategy=lambda *args, **kwargs: False,
        collect_stock_daily_trading=lambda *args, **kwargs: {},
        display_quant=lambda *args, **kwargs: None,
        format_trading_data=lambda *args, **kwargs: [],
        pre_sdt_check=lambda *args, **kwargs: True,
        setup_realtime_sdt=lambda *args, **kwargs: [],
        start_quant_analysis=lambda *args, **kwargs: [],
    ),
)

range_breakout = importlib.import_module('analysis.range_breakout_strategy')


class TestRangeBreakoutPattern(unittest.TestCase):

    @staticmethod
    def _day(close_price, ma60, ma120):
        return {
            'close_price': close_price,
            'short_ma': ma60,
            'long_ma': ma120,
        }

    def test_match_same_day_double_breakout(self):
        snapshots = [
            self._day(9.6, 10.0, 10.5),
            self._day(10.8, 10.1, 10.6),
        ]

        result = range_breakout.is_range_breakout_pattern(snapshots)

        self.assertTrue(result)

    def test_match_three_day_staggered_breakout_after_five_days_below(self):
        snapshots = [
            self._day(9.0, 10.0, 11.0),
            self._day(9.1, 10.0, 11.0),
            self._day(9.2, 10.0, 11.0),
            self._day(9.3, 10.0, 11.0),
            self._day(9.4, 10.0, 11.0),
            self._day(10.2, 10.0, 11.0),
            self._day(11.2, 10.1, 11.0),
            self._day(11.4, 10.2, 11.1),
        ]

        result = range_breakout.is_range_breakout_pattern(snapshots)

        self.assertTrue(result)

    def test_reject_when_prior_five_days_are_not_all_below_two_ma(self):
        snapshots = [
            self._day(10.2, 10.0, 11.0),
            self._day(9.1, 10.0, 11.0),
            self._day(9.2, 10.0, 11.0),
            self._day(9.3, 10.0, 11.0),
            self._day(9.4, 10.0, 11.0),
            self._day(10.2, 10.0, 11.0),
            self._day(11.2, 10.1, 11.0),
            self._day(11.4, 10.2, 11.1),
        ]

        result = range_breakout.is_range_breakout_pattern(snapshots)

        self.assertFalse(result)

    def test_reject_when_qr_date_is_not_above_any_ma(self):
        snapshots = [
            self._day(9.0, 10.0, 11.0),
            self._day(9.1, 10.0, 11.0),
            self._day(9.2, 10.0, 11.0),
            self._day(9.3, 10.0, 11.0),
            self._day(9.4, 10.0, 11.0),
            self._day(10.2, 10.0, 11.0),
            self._day(11.2, 10.1, 11.0),
            self._day(10.1, 10.2, 11.1),
        ]

        result = range_breakout.is_range_breakout_pattern(snapshots)

        self.assertFalse(result)

    def test_match_when_qr_date_is_above_only_one_ma(self):
        snapshots = [
            self._day(9.0, 10.0, 11.0),
            self._day(9.1, 10.0, 11.0),
            self._day(9.2, 10.0, 11.0),
            self._day(9.3, 10.0, 11.0),
            self._day(9.4, 10.0, 11.0),
            self._day(10.2, 10.0, 11.0),
            self._day(11.2, 10.1, 11.0),
            self._day(10.8, 10.2, 11.1),
        ]

        result = range_breakout.is_range_breakout_pattern(snapshots)

        self.assertTrue(result)


class TestRangeBreakoutDayFilters(unittest.TestCase):

    @staticmethod
    def _day(close_price, ma60, ma120):
        return {
            'close_price': close_price,
            'short_ma': ma60,
            'long_ma': ma120,
        }

    def test_reject_when_today_close_is_lower_than_yesterday_close(self):
        snapshots = [
            self._day(8.0, 7.0, 7.5),
            self._day(8.1, 7.0, 7.5),
            self._day(8.2, 7.1, 7.6),
            self._day(8.3, 7.1, 7.6),
            self._day(8.4, 7.2, 7.7),
            self._day(8.5, 7.2, 7.7),
            self._day(8.6, 7.3, 7.8),
            self._day(8.7, 7.3, 7.8),
            self._day(8.8, 7.4, 7.9),
            self._day(8.9, 7.4, 7.9),
            self._day(9.5, 9.0, 11.0),
            self._day(9.4, 9.1, 11.5),
        ]

        result = range_breakout.is_valid_breakout_day(snapshots)

        self.assertFalse(result)

    def test_reject_when_today_close_is_not_higher_than_previous_ten_closes(self):
        snapshots = [
            self._day(8.0, 7.0, 7.5),
            self._day(8.1, 7.0, 7.5),
            self._day(8.2, 7.1, 7.6),
            self._day(8.3, 7.1, 7.6),
            self._day(8.4, 7.2, 7.7),
            self._day(8.5, 7.2, 7.7),
            self._day(8.6, 7.3, 7.8),
            self._day(8.7, 7.3, 7.8),
            self._day(8.8, 7.4, 7.9),
            self._day(10.0, 7.4, 7.9),
            self._day(9.5, 9.0, 11.0),
            self._day(9.6, 9.1, 11.5),
        ]

        result = range_breakout.is_valid_breakout_day(snapshots)

        self.assertFalse(result)

    def test_reject_when_today_close_is_above_ma_but_does_not_break_any_ma(self):
        snapshots = [
            self._day(8.0, 7.0, 7.5),
            self._day(8.1, 7.0, 7.5),
            self._day(8.2, 7.1, 7.6),
            self._day(8.3, 7.1, 7.6),
            self._day(8.4, 7.2, 7.7),
            self._day(8.5, 7.2, 7.7),
            self._day(8.6, 7.3, 7.8),
            self._day(8.7, 7.3, 7.8),
            self._day(8.8, 7.4, 7.9),
            self._day(8.9, 7.4, 7.9),
            self._day(9.5, 9.0, 11.0),
            self._day(9.8, 9.1, 11.5),
        ]

        result = range_breakout.is_valid_breakout_day(snapshots)

        self.assertFalse(result)

    def test_accept_when_today_close_breaks_above_one_ma_and_meets_other_rules(self):
        snapshots = [
            self._day(8.0, 7.0, 7.5),
            self._day(8.1, 7.0, 7.5),
            self._day(8.2, 7.1, 7.6),
            self._day(8.3, 7.1, 7.6),
            self._day(8.4, 7.2, 7.7),
            self._day(8.5, 7.2, 7.7),
            self._day(8.6, 7.3, 7.8),
            self._day(8.7, 7.3, 7.8),
            self._day(8.8, 7.4, 7.9),
            self._day(8.9, 7.4, 7.9),
            self._day(9.0, 9.1, 11.0),
            self._day(9.8, 9.1, 11.5),
        ]

        result = range_breakout.is_valid_breakout_day(snapshots)

        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
