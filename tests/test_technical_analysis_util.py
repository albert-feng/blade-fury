import datetime
import importlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch


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
    'tushare',
    SimpleNamespace(
        pro_api=lambda *args, **kwargs: object(),
        get_k_data=lambda *args, **kwargs: None,
    ),
)
sys.modules.setdefault(
    'pandas',
    SimpleNamespace(
        DataFrame=type('DataFrame', (), {}),
        set_option=lambda *args, **kwargs: None,
        reset_option=lambda *args, **kwargs: None,
        isna=lambda value: value is None,
    ),
)
sys.modules.setdefault(
    'mongoengine',
    SimpleNamespace(
        connect=lambda *args, **kwargs: None,
        Document=_FakeDocument,
        StringField=_FakeField,
        DateTimeField=_FakeField,
        IntField=_FakeField,
        FloatField=_FakeField,
        BooleanField=_FakeField,
        Q=_FakeQ,
    ),
)
sys.modules.setdefault(
    'config',
    SimpleNamespace(
        mongodb_config={'db': 'test'},
        eastmoney_stock_api='http://example.com',
        tushare_token='test-token',
    ),
)
sys.modules.setdefault(
    'collector.collect_util',
    SimpleNamespace(
        get_tushare_month_trading=lambda *args, **kwargs: None,
    ),
)

util = importlib.import_module('analysis.technical_analysis_util')


class TestYearMaPreCheck(unittest.TestCase):

    def setUp(self):
        self.qr_date = datetime.datetime(2026, 9, 2)

    @patch.object(util, 'is_above_year_ma', return_value=False, create=True)
    @patch.object(util.SDT, 'objects', create=True)
    def test_pre_sdt_check_rejects_stock_below_year_ma_when_enabled(
        self,
        objects_mock,
        above_year_ma_mock,
    ):
        objects_mock.return_value.order_by.return_value = [object()]

        result = util.pre_sdt_check(
            '000001',
            qr_date=self.qr_date,
            require_above_year_ma=True,
        )

        self.assertFalse(result)
        above_year_ma_mock.assert_called_once_with(
            '000001',
            qr_date=self.qr_date,
            require_above_year_ma=True,
        )

    @patch.object(util, 'is_above_year_ma', return_value=False, create=True)
    @patch.object(util.SDT, 'objects', create=True)
    def test_pre_sdt_check_skips_year_ma_filter_when_disabled(
        self,
        objects_mock,
        above_year_ma_mock,
    ):
        objects_mock.return_value.order_by.return_value = [object()]

        result = util.pre_sdt_check(
            '000001',
            qr_date=self.qr_date,
            require_above_year_ma=False,
        )

        self.assertTrue(result)
        above_year_ma_mock.assert_not_called()

    @patch.object(util, 'is_above_year_ma', return_value=False, create=True)
    @patch.object(util.SWT, 'objects', create=True)
    def test_pre_swt_check_rejects_stock_below_year_ma_when_enabled(
        self,
        objects_mock,
        above_year_ma_mock,
    ):
        objects_mock.return_value.order_by.return_value = [object()]

        result = util.pre_swt_check(
            '000001',
            qr_date=self.qr_date,
            require_above_year_ma=True,
        )

        self.assertFalse(result)
        above_year_ma_mock.assert_called_once_with(
            '000001',
            qr_date=self.qr_date,
            require_above_year_ma=True,
        )

    @patch.object(util, 'cal_half_year_ma', return_value=8, create=True)
    @patch.object(util, 'cal_year_ma')
    @patch.object(util.SDT, 'objects', create=True)
    def test_is_above_year_ma_falls_back_to_half_year_ma_when_data_less_than_250(
        self,
        objects_mock,
        year_ma_mock,
        half_year_ma_mock,
    ):
        trading = [SimpleNamespace(today_closing_price=10, year_ma=0)] + [
            SimpleNamespace(today_closing_price=9, year_ma=0) for _ in range(149)
        ]
        objects_mock.return_value.order_by.return_value = trading

        result = util.is_above_year_ma('000001', qr_date=self.qr_date)

        self.assertTrue(result)
        year_ma_mock.assert_not_called()
        half_year_ma_mock.assert_called_once()

    @patch.object(util, 'cal_half_year_ma', create=True)
    @patch.object(util, 'cal_year_ma')
    @patch.object(util.SDT, 'objects', create=True)
    def test_is_above_year_ma_returns_false_when_data_less_than_120(
        self,
        objects_mock,
        year_ma_mock,
        half_year_ma_mock,
    ):
        trading = [SimpleNamespace(today_closing_price=10, year_ma=0) for _ in range(100)]
        objects_mock.return_value.order_by.return_value = trading

        result = util.is_above_year_ma('000001', qr_date=self.qr_date)

        self.assertFalse(result)
        year_ma_mock.assert_not_called()
        half_year_ma_mock.assert_not_called()


if __name__ == '__main__':
    unittest.main()
