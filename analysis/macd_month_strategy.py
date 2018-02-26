#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'fengweigang'


import argparse
import datetime
import logging

from models import QuantResult as QR
from logger import setup_logging
from analysis.technical_analysis_util import start_quant_analysis, pre_sdt_check, get_month_trading
from analysis.technical_analysis_util import calculate_macd, check_duplicate_strategy


def quant_stock(stock_number, stock_name, **kwargs):
    short_ema = kwargs['short_ema']
    long_ema = kwargs['long_ema']
    dif_ema = kwargs['dif_ema']
    qr_date = kwargs['qr_date']
    if not pre_sdt_check(stock_number, **kwargs):
        return

    strategy_direction = 'long'
    strategy_name = 'month_macd_%s_%s_%s_%s' % (strategy_direction, short_ema, long_ema, dif_ema)

    end_date = qr_date.strftime('%Y-%m-%d')
    start_date = (qr_date - datetime.timedelta(days=short_ema * long_ema * 31)).strftime('%Y-%m-%d')

    trading_data = get_month_trading(stock_number, start_date, end_date)
    trading_data = trading_data.iloc[-150:]

    if len(trading_data) < max(short_ema, long_ema):
        return

    df = calculate_macd(trading_data, short_ema, long_ema, dif_ema)
    this_month = df.iloc[-1]
    last_month = df.iloc[-2]

    if last_month['macd'] < 0 < this_month['macd']:
        init_price = this_month['close_price']
        increase_rate = round((this_month['close_price'] - last_month['close_price']) / last_month['close_price'],
                              4) * 100
        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=this_month.name,
            strategy_direction=strategy_direction, strategy_name=strategy_name,
            init_price=init_price, industry_involved=kwargs.get('industry_involved'),
            increase_rate=increase_rate
        )
        if not check_duplicate_strategy(qr):
            qr.save()
            return qr
    return


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据长短均线的金叉来选股')
    parser.add_argument(u'-s', action=u'store', dest='short_ema', required=True, help=u'短期指数加权均线数')
    parser.add_argument(u'-l', action=u'store', dest='long_ema', required=True, help=u'长期指数加权均线数')
    parser.add_argument(u'-d', action=u'store', dest='dif_ema', required=True, help=u'dif指数加权均线数')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算策略的日期')

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

    return int(args.short_ema), int(args.long_ema), int(args.dif_ema), qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    short_ema, long_ema, dif_ema, qr_date = setup_argparse()

    real_time_res = start_quant_analysis(short_ema=short_ema, long_ema=long_ema, dif_ema=dif_ema, qr_date=qr_date,
                                         quant_stock=quant_stock)
