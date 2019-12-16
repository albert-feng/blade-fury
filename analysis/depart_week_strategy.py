#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import argparse
import pandas as pd

from mongoengine import Q
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockWeeklyTrading as SWT
from analysis.technical_analysis_util import calculate_macd, format_trading_data, calculate_ma, start_quant_analysis, \
    check_duplicate_strategy, is_ad_price


period = 3
ema_volume = 150
short_ma = 5
long_ma = 10
short_ema = 12
long_ema = 26
dif_ema = 9


def quant_stock(stock_number, stock_name, **kwargs):
    qr_date = kwargs['qr_date']

    strategy_name = "depart_long_week"
    last_trade_date = qr_date + datetime.timedelta(days=7)
    swt = SWT.objects(Q(stock_number=stock_number) &
                      Q(last_trade_date__lte=last_trade_date)).order_by('-last_trade_date')[:ema_volume]
    use_ad_price, swt = is_ad_price(stock_number, qr_date, swt)
    if not swt:
        return

    trading_data = format_trading_data(swt, use_ad_price)
    df = calculate_macd(DataFrame(trading_data), short_ema, long_ema, dif_ema)
    df = calculate_ma(df, short_ma, long_ma)
    this_week = df.iloc[-1]
    last_week = df.iloc[-2]

    if last_week['close_price'] < last_week['long_ma'] and this_week['close_price'] > this_week['short_ma']\
       and this_week['close_price'] > this_week['long_ma']:
        if use_ad_price:
            init_price = swt[0].weekly_close_price
        else:
            init_price = this_week['close_price']

        increase_rate = round((this_week['close_price'] - last_week['close_price']) / last_week['close_price'], 4) * 100

        short_point = -1
        for i in range(1, len(df)):
            if df.iloc[-i].diff_ma > 0:
                short_point = i
                break

        # if short_point < period:
        #     return

        if df.iloc[-short_point:].macd.sum() > 0:
            # print(stock_number)
            # pd.set_option('display.max_columns', 500)
            # pd.set_option('display.width', 1000)
            # print(df.iloc[-short_point:])

            qr = QR(
                stock_number=stock_number, stock_name=stock_name, date=qr_date,
                strategy_direction='long', strategy_name=strategy_name, init_price=init_price,
                industry_involved=kwargs.get('industry_involved'), increase_rate=increase_rate
            )
            if not check_duplicate_strategy(qr):
                qr.save()
                return qr


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据周线背离来选股')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算周线背离策略的日期')

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

    return qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    qr_date = setup_argparse()
    start_quant_analysis(qr_date=qr_date, quant_stock=quant_stock)

