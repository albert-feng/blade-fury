#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import argparse

from mongoengine import Q
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import collect_stock_daily_trading, start_quant_analysis, format_trading_data
from analysis.technical_analysis_util import pre_sdt_check, check_duplicate_strategy, display_quant, setup_realtime_sdt


def quant_stock(stock_number, stock_name, **kwargs):
    length = kwargs['length']
    qr_date = kwargs['qr_date']
    real_time = kwargs.get('real_time', False)
    if not pre_sdt_check(stock_number, qr_date):
        return

    strategy_name = 'new_peak_%s' % length
    strategy_direction = 'long'

    sdt = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) &
                      Q(date__lte=qr_date)).order_by('-date')[:length]
    if len(sdt) < length:
        return

    if real_time:
        sdt = setup_realtime_sdt(stock_number, sdt, kwargs)
    trading_data = format_trading_data(sdt)
    if not trading_data:
        return

    df = DataFrame(trading_data)
    today_data = df.iloc[-1]

    if df['close_price'].max() <= today_data['close_price']:
        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=today_data.date,
            strategy_direction=strategy_direction, strategy_name=strategy_name,
            init_price=today_data['close_price'], industry_involved=kwargs.get('industry_involved'),
            increase_rate=sdt[0].increase_rate
        )
        if real_time:
            return qr
        if not check_duplicate_strategy(qr):
            qr.save()
            return qr
    return


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据股价是否新高来选股')
    parser.add_argument(u'-l', action=u'store', dest='length', required=True, help=u'计算新高周期数')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算新高的日期')
    parser.add_argument(u'-r', action=u'store_true', dest='real_time', required=False, help=u'是否实时计算')

    args = parser.parse_args()
    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y-%m-%d')
        except Exception as e:
            print('Wrong date form')
            raise e
    else:
        today = datetime.date.today()
        qr_date = datetime.datetime(year=today.year, month=today.month, day=today.day)

    return int(args.length), qr_date, args.real_time


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    length, qr_date, real_time = setup_argparse()
    today_trading = {}
    if real_time:
        today_trading = collect_stock_daily_trading()

    real_time_res = start_quant_analysis(length=length, qr_date=qr_date, quant_stock=quant_stock,
                                         real_time=real_time, today_trading=today_trading)
    if real_time_res and real_time:
        display_quant(real_time_res)
