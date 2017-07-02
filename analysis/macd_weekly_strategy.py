#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
import argparse
import logging

from mongoengine import Q
from pandas import DataFrame

from analysis.technical_analysis_util import check_year_ma, calculate_macd, check_duplicate_strategy
from analysis.technical_analysis_util import format_trading_data, start_quant_analysis
from models import StockWeeklyTrading as SWT, StockDailyTrading as SDT
from models import QuantResult as QR
from logger import setup_logging


def quant_stock(stock_number, stock_name, **kwargs):
    short_ema = kwargs['short_ema']
    long_ema = kwargs['long_ema']
    dif_ema = kwargs['dif_ema']
    qr_date = kwargs['qr_date']
    if not check_year_ma(stock_number, qr_date):
        return

    strategy_direction = 'long'
    quant_count = 150

    strategy_name = 'macdweek_%s_%s_%s_%s' % (strategy_direction, short_ema, long_ema, dif_ema)

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
        trading_data.insert(0, extra_data)
    df = calculate_macd(DataFrame(trading_data), short_ema, long_ema, dif_ema)
    today_macd = df.iloc[-1]
    yestoday_macd = df.iloc[-2]

    if yestoday_macd['macd'] < 0 < today_macd['macd']:
        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=today_macd.name,
            strategy_direction=strategy_direction, strategy_name=strategy_name, init_price=today_macd['close_price']
        )
        if not check_duplicate_strategy(qr):
            qr.save()


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
        except Exception, e:
            print 'Wrong date form'
            raise e
    else:
        qr_date = datetime.date.today()

    return int(args.short_ema), int(args.long_ema), int(args.dif_ema), qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    short_ema, long_ema, dif_ema, qr_date = setup_argparse()

    real_time_res = start_quant_analysis(short_ema=short_ema, long_ema=long_ema, dif_ema=dif_ema, qr_date=qr_date,
                                         quant_stock=quant_stock)
