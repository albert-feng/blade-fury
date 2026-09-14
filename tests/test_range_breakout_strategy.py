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

    def test_reject_when_qr_date_is_not_above_both_ma(self):
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

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
