#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'fengweigang'

import tushare as ts
import datetime
import logging
import argparse

from logger import setup_logging
from models import QuantResult as QR
from analysis.technical_analysis_util import calculate_ma, check_duplicate_strategy
from analysis.technical_analysis_util import start_quant_analysis, pre_sdt_check


def get_month_trading(stock_number, start_date, end_date):
    month_trading_data = ts.get_k_data(stock_number, ktype='M', autype='qfq', start=start_date, end=end_date)
    df = month_trading_data.set_index(['date'])
    df['close_price'] = df['close']
    return df


def quant_stock(stock_number, stock_name, **kwargs):
    short_ma = kwargs['short_ma']
    long_ma = kwargs['long_ma']
    qr_date = kwargs['qr_date']
    if not pre_sdt_check(stock_number, **kwargs):
        return

    if short_ma < long_ma:
        strategy_direction = 'long'
    else:
        strategy_direction = 'short'
    strategy_name = 'month_through_%s_%s_%s' % (strategy_direction, short_ma, long_ma)

    end_date = qr_date.strftime('%Y-%m-%d')
    start_date = (qr_date - datetime.timedelta(days=max(short_ma, long_ma)*31)).strftime('%Y-%m-%d')
    df = calculate_ma(get_month_trading(stock_number, start_date, end_date), short_ma, long_ma)
    this_month = df.iloc[-1]
    last_month = df.iloc[-2]

    if last_month['close_price'] < last_month['long_ma'] and this_month['close_price'] > this_month['short_ma'] \
            and this_month['close_price'] > this_month['long_ma']:
        init_price = this_month['close_price']
        increase_rate = round((this_month['close_price'] - last_month['close_price']) / last_month['close_price'], 4) * 100
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
