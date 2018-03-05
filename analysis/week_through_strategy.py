#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
author: albert feng
description:
"""


import datetime
import logging
import argparse

from mongoengine import Q
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockWeeklyTrading as SWT
from analysis.technical_analysis_util import calculate_ma, format_trading_data, check_duplicate_strategy
from analysis.technical_analysis_util import start_quant_analysis, pre_sdt_check, is_ad_price


def quant_stock(stock_number, stock_name, **kwargs):
    short_ma = kwargs['short_ma']
    long_ma = kwargs['long_ma']
    qr_date = kwargs['qr_date']
    if not pre_sdt_check(stock_number, **kwargs):
        return

    if short_ma < long_ma:
        strategy_direction = 'long'
        quant_count = long_ma + 5
    else:
        strategy_direction = 'short'
        quant_count = short_ma + 5
    strategy_name = 'week_through_%s_%s_%s' % (strategy_direction, short_ma, long_ma)

    last_trade_date = qr_date + datetime.timedelta(days=7)
    swt = SWT.objects(Q(stock_number=stock_number) &
                      Q(last_trade_date__lte=last_trade_date)).order_by('-last_trade_date')[:quant_count]

    use_ad_price, swt = is_ad_price(stock_number, qr_date, swt)
    if not swt:
        return

    trading_data = format_trading_data(swt, use_ad_price)
    df = calculate_ma(DataFrame(trading_data), short_ma, long_ma)
    this_week = df.iloc[-1]
    last_week = df.iloc[-2]

    if last_week['close_price'] < last_week['long_ma'] and this_week['close_price'] > this_week['short_ma']\
       and this_week['close_price'] > this_week['long_ma']:
        if use_ad_price:
            init_price = swt[0].weekly_close_price
        else:
            init_price = this_week['close_price']

        increase_rate = round((this_week['close_price'] - last_week['close_price']) / last_week['close_price'], 4) * 100
        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=qr_date,
            strategy_direction=strategy_direction, strategy_name=strategy_name, init_price=init_price,
            industry_involved=kwargs.get('industry_involved'), increase_rate=increase_rate
        )
        if not check_duplicate_strategy(qr):
            qr.save()
            return qr
    return


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据长短均线的金叉来选股')
    parser.add_argument(u'-s', action=u'store', dest='short_ma', required=True, help=u'短期均线数')
    parser.add_argument(u'-l', action=u'store', dest='long_ma', required=True, help=u'长期均线数')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算均线的日期')

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

    return int(args.short_ma), int(args.long_ma), qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    short_ma, long_ma, qr_date = setup_argparse()

    real_time_res = start_quant_analysis(short_ma=short_ma, long_ma=long_ma, qr_date=qr_date, quant_stock=quant_stock)
