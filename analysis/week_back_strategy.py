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
from analysis.technical_analysis_util import format_trading_data, check_duplicate_strategy
from analysis.technical_analysis_util import start_quant_analysis, pre_swt_check, is_ad_price


def quant_stock(stock_number, stock_name, **kwargs):
    ma_window = kwargs['long_ma']
    qr_date = kwargs['qr_date']

    if not pre_swt_check(stock_number, **kwargs):
        return

    strategy_direction = 'long'
    strategy_name = 'week_back_long_%s' % ma_window

    # Need enough data to calculate MA for the last 3 weeks
    quant_count = ma_window + 5

    last_trade_date = qr_date + datetime.timedelta(days=7)
    swt = SWT.objects(Q(stock_number=stock_number) &
                      Q(last_trade_date__lte=last_trade_date)).order_by('-last_trade_date')[:quant_count]

    if not swt or len(swt) < 3:
        return

    use_ad_price, swt = is_ad_price(stock_number, qr_date, swt)
    if not swt:
        return

    trading_data = format_trading_data(swt, use_ad_price)
    df = DataFrame(trading_data)

    if len(df) < ma_window:
        return

    # Calculate MA
    df['ma'] = df['close_price'].rolling(window=ma_window, center=False).mean()

    # Ensure we have enough data points with MA calculated
    # We need index -1, -2, -3
    if len(df) < 3:
        return

    # 倒数第一周 (Last week, index -1)
    week_1 = df.iloc[-1]
    # 倒数第二周 (2nd last week, index -2)
    week_2 = df.iloc[-2]
    # 倒数第3周 (3rd last week, index -3)
    week_3 = df.iloc[-3]

    # Check for NaN in MA (if not enough data for MA)
    if pd.isna(week_1['ma']) or pd.isna(week_2['ma']) or pd.isna(week_3['ma']):
        return

    # Logic:
    # 倒数第3周的收盘价大于等于均线值
    cond1 = week_3['close_price'] >= week_3['ma']
    # 倒数第二周的收盘价小于等于均线值
    cond2 = week_2['close_price'] <= week_2['ma']
    # 倒数第一周的收盘价大于等于均线值
    cond3 = week_1['close_price'] >= week_1['ma']

    if cond1 and cond2 and cond3:
        if use_ad_price:
            init_price = swt[0].weekly_close_price
        else:
            init_price = week_1['close_price']

        increase_rate = round((week_1['close_price'] - week_2['close_price']) / week_2['close_price'], 4) * 100

        # 周线：当周成交额（单位万）换算为“亿”并保留两位小数
        week_turnover_raw = swt[0].turnover_amount
        turnover_amount_str = f"{week_turnover_raw / 10000:.2f}亿"

        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=qr_date,
            strategy_direction=strategy_direction, strategy_name=strategy_name,
            init_price=init_price, industry_involved=kwargs.get('industry_involved'),
            increase_rate=increase_rate, turnover_amount=turnover_amount_str
        )

        if not check_duplicate_strategy(qr):
            qr.save()
            return qr
    return


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'周线回归策略')
    parser.add_argument(u'-l', action=u'store', dest='long_ma', required=True, help=u'均线周期')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算日期')

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

    return int(args.long_ma), qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    long_ma, qr_date = setup_argparse()

    start_quant_analysis(long_ma=long_ma, qr_date=qr_date, quant_stock=quant_stock)
