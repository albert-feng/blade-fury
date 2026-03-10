#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
import logging
import pandas as pd
from pandas import DataFrame
from mongoengine import Q

from logger import setup_logging
from models import QuantResult as QR, StockWeeklyTrading as SWT, StockDailyTrading as SDT
from analysis.technical_analysis_util import format_trading_data, check_duplicate_strategy, start_quant_analysis, pre_swt_check


def quant_stock(stock_number, stock_name, **kwargs):
    ma_window = kwargs['ma_window']
    qr_date = kwargs['qr_date']

    if not pre_swt_check(stock_number, **kwargs):
        return

    # 检查是否有当日的日k线数据，如果没有则跳过
    if not SDT.objects(stock_number=stock_number, date=qr_date):
        return

    strategy_direction = 'long'
    strategy_name = 'weekly_support_%s' % ma_window

    # Need enough data:
    # 1. Calculate MA (needs ma_window)
    # 2. Check last 10 weeks increase (needs 10 weeks + 1 for pct_change)
    quant_count = max(ma_window, 12) + 5

    # Use similar logic to week_back_strategy for date handling
    last_trade_date = qr_date + datetime.timedelta(days=7)
    swt = SWT.objects(Q(stock_number=stock_number)
                      & Q(last_trade_date__lte=last_trade_date)).order_by('-last_trade_date')[:quant_count]

    if not swt or len(swt) < 10:
        return

    # format_trading_data sorts by date ascending
    trading_data = format_trading_data(swt)
    df = DataFrame(trading_data)

    if len(df) < ma_window:
        return

    # Calculate MA
    df['ma'] = df['close_price'].rolling(window=ma_window, center=False).mean()

    # Calculate pct_change
    df['pct_change'] = df['close_price'].pct_change(fill_method=None)

    # Ensure we have enough data for 10-week check
    if len(df) < 11:
        return

    # Condition 1: At least one week in previous 10 weeks (excluding current week) with increase > 9%
    prev_10_weeks = df.iloc[-11:-1]

    # Check single week > 9%
    has_single_surge = any(prev_10_weeks['pct_change'] > 0.09)

    if not has_single_surge:
        return

    # Condition 2: Current week (last row) Close > MA > Low
    current_week = df.iloc[-1]

    # Check if MA is valid (not NaN)
    if pd.isna(current_week['ma']):
        return

    # Condition 3: Current week must be rising
    if current_week['pct_change'] <= 0:
        return

    if current_week['close_price'] >= current_week['ma'] >= current_week['low_price']:
        init_price = current_week['close_price']
        increase_rate = round(current_week['pct_change'] * 100, 2) if not pd.isna(current_week['pct_change']) else 0

        # Turnover amount (万 -> 亿)
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
    parser = argparse.ArgumentParser(description=u'周均线支撑策略')
    parser.add_argument(u'-m', action=u'store', dest='ma_window', required=True, help=u'均线周期')
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

    return int(args.ma_window), qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    ma_window, qr_date = setup_argparse()

    start_quant_analysis(ma_window=ma_window, qr_date=qr_date, quant_stock=quant_stock)
