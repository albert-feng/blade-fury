#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
import logging

import pandas as pd
from mongoengine import Q
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import (
    calculate_macd,
    check_duplicate_strategy,
    format_trading_data,
    pre_sdt_check,
    start_quant_analysis,
)


def quant_stock(stock_number, stock_name, **kwargs):
    qr_date = kwargs['qr_date']

    if not pre_sdt_check(stock_number, **kwargs):
        return

    if not SDT.objects(stock_number=stock_number, date=qr_date):
        return

    strategy_direction = 'long'
    strategy_name = 'dif60_below_break'

    quant_count = 200
    sdt = SDT.objects(Q(stock_number=stock_number) & Q(date__lte=qr_date)).order_by('-date')[:quant_count]
    if not sdt or len(sdt) < 100:
        return

    trading_data = format_trading_data(sdt)
    df = DataFrame(trading_data)
    if len(df) < 100:
        return

    df = calculate_macd(df, 12, 26, 9)
    if 'dif' not in df:
        return

    df['pct_change'] = df['close_price'].pct_change(fill_method=None)

    today = df.iloc[-1]
    if pd.isna(today['dif']):
        return

    prev_60_days = df['dif'].iloc[-61:-1]
    if len(prev_60_days) != 60:
        return
    if prev_60_days.isna().any():
        return

    if not (prev_60_days < 0).all():
        return

    if today['dif'] <= 0:
        return

    increase_rate = round(today['pct_change'] * 100, 2) if not pd.isna(today['pct_change']) else 0

    turnover_amount = 0
    if sdt[0].date.date() == df.index[-1].date():
        turnover_amount = sdt[0].turnover_amount
    turnover_amount_str = f"{turnover_amount / 100000:.2f}亿"

    qr = QR(
        stock_number=stock_number,
        stock_name=stock_name,
        date=qr_date,
        strategy_direction=strategy_direction,
        strategy_name=strategy_name,
        init_price=float(today['close_price']),
        industry_involved=kwargs.get('industry_involved'),
        increase_rate=increase_rate,
        turnover_amount=turnover_amount_str,
    )

    if not check_duplicate_strategy(qr):
        qr.save()
        return qr
    return


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'DIF连续60日小于0后当日上穿0策略')
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

    return qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    qr_date = setup_argparse()
    start_quant_analysis(qr_date=qr_date, quant_stock=quant_stock)
