#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
import logging
import argparse

from mongoengine import Q
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT, StockWeeklyTrading as SWT
from analysis.technical_analysis_util import calculate_ma, format_trading_data, check_duplicate_strategy
from analysis.technical_analysis_util import start_quant_analysis, check_year_ma


def quant_stock(stock_number, stock_name, **kwargs):
    short_ma = kwargs['short_ma']
    long_ma = kwargs['long_ma']
    qr_date = kwargs['qr_date']
    if not check_year_ma(stock_number, qr_date):
        return

    if short_ma < long_ma:
        strategy_direction = 'long'
        quant_count = long_ma + 5
    else:
        strategy_direction = 'short'
        quant_count = short_ma + 5
    strategy_name = 'maweek_%s_%s_%s' % (strategy_direction, short_ma, long_ma)

    swt = SWT.objects(Q(stock_number=stock_number) &
                      Q(last_trade_date__lte=qr_date)).order_by('-last_trade_date')[:quant_count]
    if not swt:
        return

    extra_data = dict()
    if swt[0].last_trade_date < qr_date:
        # 当没有当周数据时，用日线数据补
        sdt = SDT.objects(Q(stock_number=stock_number) & Q(date=qr_date))
        if not sdt:
            return

        qr_date_trading = sdt[0]
        extra_data['close_price'] = qr_date_trading.today_closing_price
        extra_data['date'] = qr_date_trading.date

    trading_data = format_trading_data(swt)
    if extra_data:
        trading_data.append(extra_data)
    df = calculate_ma(DataFrame(trading_data), short_ma, long_ma)
    today_ma = df.iloc[-1]
    yestoday_ma = df.iloc[-2]

    if today_ma['diff_ma'] > 0 > yestoday_ma['diff_ma']:
        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=today_ma.name,
            strategy_direction=strategy_direction, strategy_name=strategy_name,
            init_price=today_ma['close_price']
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
            print 'Wrong date form'
            raise e
    else:
        today = datetime.date.today()
        qr_date = datetime.datetime(year=today.year, month=today.month, day=today.day)

    return int(args.short_ma), int(args.long_ma), qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    short_ma, long_ma, qr_date = setup_argparse()

    real_time_res = start_quant_analysis(short_ma=short_ma, long_ma=long_ma, qr_date=qr_date, quant_stock=quant_stock)
