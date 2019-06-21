#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
背离策略
"""

import argparse
import logging
import datetime
from pandas import DataFrame

from mongoengine import Q

from logger import setup_logging
from collector import tushare_util
from models import StockDailyTrading as SDT
from analysis.technical_analysis_util import start_quant_analysis, format_trading_data, calculate_ma, calculate_macd


ema_volume = 150
quant_days = 210


def quant_stock(stock_number, stock_name, **kwargs):
    sdt = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) &
                          Q(date__lte=kwargs['qr_date'])).order_by('-date')[:ema_volume]

    if float(sdt[0].increase_rate.replace('%', '')) > 9:
        return

    trading_data = format_trading_data(sdt)
    df = calculate_ma(DataFrame(trading_data), kwargs['short_ma'], kwargs['long_ma'])
    df = calculate_macd(df, kwargs['short_ema'], kwargs['long_ema'], kwargs['dif_ema'])
    today = df.iloc[-1]
    yestoday = df.iloc[-2]


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据突破短均线的策略选股')
    parser.add_argument(u'-s', action=u'store', dest='short_ma', required=True, help=u'短期均线')
    parser.add_argument(u'-l', action=u'store', dest='long_ma', required=True, help=u'长期均线')
    parser.add_argument(u'-se', action=u'store', dest='short_ema', required=True, help=u'短期指数加权均线')
    parser.add_argument(u'-le', action=u'store', dest='long_ema', required=True, help=u'长期指数加权均线')
    parser.add_argument(u'-d', action=u'store', dest='dif_ema', required=True, help=u'dif指数加权均线数')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'执行策略的日期')
    # parser.add_argument(u'-r', action=u'store_true', dest='real_time', required=False, help=u'是否实时计算')

    args = parser.parse_args()

    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y-%m-%d').date()
        except Exception as e:
            print('Wrong date form')
            raise e
    else:
        qr_date = datetime.date.today()

    return int(args.short_ma), int(args.long_ma), int(args.short_ema), int(args.long_ema), int(args.dif_ema), \
        qr_date, args.real_time


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    short_ma, long_ma, short_ema, long_ema, dif_ema, qr_date, real_time = setup_argparse()
    quant_result = start_quant_analysis(short_ma=short_ma, long_ma=long_ma, short_ema=short_ema, long_ema=long_ema, dif_ema=dif_ema,
                                        qr_date=qr_date, real_time=real_time, quant_stock=quant_stock)






