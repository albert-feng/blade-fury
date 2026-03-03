#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
import logging
import pandas as pd
from pandas import DataFrame
from mongoengine import Q

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import format_trading_data, check_duplicate_strategy, start_quant_analysis, pre_sdt_check


def quant_stock(stock_number, stock_name, **kwargs):
    ma_window = kwargs['ma_window']
    qr_date = kwargs['qr_date']

    if not pre_sdt_check(stock_number, **kwargs):
        return

    strategy_direction = 'long'
    strategy_name = 'ma_support_%s' % ma_window

    # Need enough data:
    # 1. Calculate MA (needs ma_window)
    # 2. Check last 10 days increase (needs 10 days + 1 for pct_change)
    quant_count = max(ma_window, 12) + 5

    sdt = SDT.objects(Q(stock_number=stock_number)
                      & Q(date__lte=qr_date)).order_by('-date')[:quant_count]

    if not sdt or len(sdt) < 10:
        return

    # format_trading_data sorts by date ascending
    trading_data = format_trading_data(sdt)
    df = DataFrame(trading_data)

    if len(df) < ma_window:
        return

    # Calculate MA
    df['ma'] = df['close_price'].rolling(window=ma_window, center=False).mean()

    # Calculate pct_change
    df['pct_change'] = df['close_price'].pct_change()

    # Ensure we have enough data for 10-day check
    if len(df) < 10:
        return

    # Condition 1: At least one day in previous 10 days (excluding today) with increase > 9%
    if len(df) < 11:
        return
    prev_10_days = df.iloc[-11:-1]
    has_surge = any(prev_10_days['pct_change'] > 0.09)
    if not has_surge:
        return

    # Condition 2: Today (last row) Close > MA > Low
    today = df.iloc[-1]

    # Check if MA is valid (not NaN)
    if pd.isna(today['ma']):
        return

    # Condition 3: Today must be rising
    if today['pct_change'] <= 0:
        return

    if today['close_price'] >= today['ma'] >= today['low_price']:
        init_price = today['close_price']
        increase_rate = round(today['pct_change'] * 100, 2) if not pd.isna(today['pct_change']) else 0

        # Turnover amount (万 -> 亿)
        # Need to fetch turnover from sdt object corresponding to today
        # Since sdt is sorted desc by query, sdt[0] is the latest if qr_date matches
        # But let's find the matching SDT object for today's date

        # Optimization: sdt[0] should be today if qr_date is latest available
        # But we queried date__lte=qr_date, so sdt[0] is the record for qr_date (or closest before)
        # df.iloc[-1] is also that record.

        # Check if sdt[0] matches df.iloc[-1]['date']
        # format_trading_data sorts sdt by date asc
        # Wait, format_trading_data takes sdt list and returns sorted list of dicts.
        # But sdt query was order_by('-date').
        # So sdt[0] is the latest date (qr_date).

        turnover_amount = 0
        if sdt[0].date.date() == today['date'].date():
            turnover_amount = sdt[0].turnover_amount

        turnover_amount_str = f"{turnover_amount / 100000:.2f}亿"

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
    parser = argparse.ArgumentParser(description=u'均线支撑策略')
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
