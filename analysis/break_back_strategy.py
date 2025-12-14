#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import argparse

from mongoengine import Q
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import format_trading_data, check_duplicate_strategy
from analysis.technical_analysis_util import start_quant_analysis, pre_sdt_check


def quant_stock(stock_number, stock_name, **kwargs):
    if not pre_sdt_check(stock_number, **kwargs):
        return

    long_ma = kwargs['long_ma']
    qr_date = kwargs['qr_date']

    sdt = SDT.objects(
        Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) & Q(date__lte=qr_date)
    ).order_by('-date')[:long_ma + 10]
    trading_data = format_trading_data(sdt)
    if not trading_data or len(trading_data) < long_ma or len(trading_data) < 3:
        return

    df = DataFrame(trading_data)
    if df.index.name != 'date':
        df = df.set_index(['date'])
    df['ma'] = df['close_price'].rolling(window=long_ma, center=False).mean()

    d3 = df.iloc[-3]
    d2 = df.iloc[-2]
    d1 = df.iloc[-1]

    if d3['close_price'] >= d3['ma'] and d2['close_price'] <= d2['ma'] and d1['close_price'] >= d1['ma']:
        strategy_direction = 'long'
        strategy_name = 'break_back_long_%s' % long_ma
        increase_rate = round((d1['close_price'] - d2['close_price']) / d2['close_price'], 4) * 100
        day_turnover_raw = sdt[0].turnover_amount
        turnover_amount_str = f"{day_turnover_raw / 100000:.2f}亿"
        qr = QR(
            stock_number=stock_number,
            stock_name=stock_name,
            date=d1.name,
            strategy_direction=strategy_direction,
            strategy_name=strategy_name,
            init_price=d1['close_price'],
            industry_involved=kwargs.get('industry_involved'),
            increase_rate=increase_rate,
            turnover_amount=turnover_amount_str
        )
        if not check_duplicate_strategy(qr):
            qr.save()
            return qr
    return


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'均线回踩突破策略选股（仅长均线）')
    parser.add_argument(u'-l', action=u'store', dest='long_ma', required=True, help=u'长期均线数')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算日期')

    args = parser.parse_args()
    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y-%m-%d')
        except Exception as e:
            print('Wrong date form')
            raise e
    else:
        qr_date = datetime.date.today()

    return int(args.long_ma), qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    long_ma, qr_date = setup_argparse()
    start_quant_analysis(long_ma=long_ma, qr_date=qr_date, quant_stock=quant_stock)
