#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
import logging

from mongoengine import Q
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import (
    calculate_ma,
    check_duplicate_strategy,
    collect_stock_daily_trading,
    display_quant,
    format_trading_data,
    pre_sdt_check,
    setup_realtime_sdt,
    start_quant_analysis,
)


SHORT_MA = 60
LONG_MA = 120
BREAKOUT_WINDOW = 3
PRE_BREAKOUT_LOOKBACK = 5
QUANT_COUNT = LONG_MA + BREAKOUT_WINDOW + PRE_BREAKOUT_LOOKBACK + 5


def _has_valid_ma(day_snapshot):
    short_ma = day_snapshot.get('short_ma')
    long_ma = day_snapshot.get('long_ma')
    return (
        short_ma is not None
        and long_ma is not None
        and short_ma == short_ma
        and long_ma == long_ma
    )


def _is_above_both_ma(day_snapshot):
    if not _has_valid_ma(day_snapshot):
        return False
    return (
        day_snapshot['close_price'] > day_snapshot['short_ma']
        and day_snapshot['close_price'] > day_snapshot['long_ma']
    )


def _is_below_both_ma(day_snapshot):
    if not _has_valid_ma(day_snapshot):
        return False
    return (
        day_snapshot['close_price'] < day_snapshot['short_ma']
        and day_snapshot['close_price'] < day_snapshot['long_ma']
    )


def _is_breaking_ma(prev_day, current_day, ma_key):
    if not _has_valid_ma(prev_day) or not _has_valid_ma(current_day):
        return False
    return (
        prev_day['close_price'] <= prev_day[ma_key]
        and current_day['close_price'] > current_day[ma_key]
    )


def _is_same_day_double_breakout(day_snapshots):
    if len(day_snapshots) < 2:
        return False

    prev_day = day_snapshots[-2]
    today = day_snapshots[-1]
    return _is_breaking_ma(prev_day, today, 'short_ma') and _is_breaking_ma(
        prev_day, today, 'long_ma'
    )


def _is_three_day_window_breakout(day_snapshots):
    required_days = PRE_BREAKOUT_LOOKBACK + BREAKOUT_WINDOW
    if len(day_snapshots) < required_days:
        return False

    today = day_snapshots[-1]
    if not _is_above_both_ma(today):
        return False

    previous_five_days = day_snapshots[-required_days:-BREAKOUT_WINDOW]
    if len(previous_five_days) != PRE_BREAKOUT_LOOKBACK:
        return False
    if not all(_is_below_both_ma(day_snapshot) for day_snapshot in previous_five_days):
        return False

    has_short_breakout = False
    has_long_breakout = False
    start_index = len(day_snapshots) - BREAKOUT_WINDOW
    for current_index in range(start_index, len(day_snapshots)):
        prev_day = day_snapshots[current_index - 1]
        current_day = day_snapshots[current_index]
        if _is_breaking_ma(prev_day, current_day, 'short_ma'):
            has_short_breakout = True
        if _is_breaking_ma(prev_day, current_day, 'long_ma'):
            has_long_breakout = True

    return has_short_breakout and has_long_breakout


def is_range_breakout_pattern(day_snapshots):
    if not day_snapshots:
        return False

    if not _is_above_both_ma(day_snapshots[-1]):
        return False

    if _is_same_day_double_breakout(day_snapshots):
        return True

    return _is_three_day_window_breakout(day_snapshots)


def quant_stock(stock_number, stock_name, **kwargs):
    qr_date = kwargs['qr_date']
    real_time = kwargs.get('real_time', False)

    if not pre_sdt_check(stock_number, **kwargs):
        return

    if not real_time and not SDT.objects(stock_number=stock_number, date=qr_date):
        return

    sdt = SDT.objects(
        Q(stock_number=stock_number)
        & Q(today_closing_price__ne=0.0)
        & Q(date__lte=qr_date)
    ).order_by('-date')[:QUANT_COUNT]
    if not sdt:
        return

    if real_time:
        sdt = setup_realtime_sdt(stock_number, sdt, kwargs)
        if not sdt:
            return

    trading_data = format_trading_data(sdt)
    if not trading_data or len(trading_data) < (LONG_MA + BREAKOUT_WINDOW + PRE_BREAKOUT_LOOKBACK):
        return

    df = calculate_ma(DataFrame(trading_data), SHORT_MA, LONG_MA)
    day_snapshots = df[['close_price', 'short_ma', 'long_ma']].to_dict('records')
    if not is_range_breakout_pattern(day_snapshots):
        return

    today = df.iloc[-1]
    yesterday = df.iloc[-2]
    increase_rate = round(
        (today['close_price'] - yesterday['close_price']) / yesterday['close_price'],
        4,
    ) * 100
    turnover_amount_str = f"{sdt[0].turnover_amount / 100000:.2f}亿"
    qr = QR(
        stock_number=stock_number,
        stock_name=stock_name,
        date=today.name,
        strategy_direction='long',
        strategy_name='range_breakout',
        init_price=today['close_price'],
        industry_involved=kwargs.get('industry_involved'),
        increase_rate=increase_rate,
        turnover_amount=turnover_amount_str,
    )

    if real_time:
        return qr
    if not check_duplicate_strategy(qr):
        qr.save()
        return qr
    return


def setup_argparse():
    parser = argparse.ArgumentParser(description='区间突破策略选股')
    parser.add_argument('-t', action='store', dest='qr_date', required=False, help='计算日期')
    parser.add_argument('-r', action='store_true', dest='real_time', required=False, help='是否实时计算')

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

    return qr_date, args.real_time


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    qr_date, real_time = setup_argparse()
    today_trading = {}
    if real_time:
        today_trading = collect_stock_daily_trading()
    real_time_res = start_quant_analysis(
        qr_date=qr_date,
        quant_stock=quant_stock,
        real_time=real_time,
        today_trading=today_trading,
        require_above_year_ma=True,
    )
    if real_time_res and real_time:
        display_quant(real_time_res)
