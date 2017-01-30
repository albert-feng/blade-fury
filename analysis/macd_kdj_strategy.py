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
from analysis.technical_analysis_util import calculate_macd, calculate_kdj, start_quant_analysis


step = 100  # 一次从数据库取出打股票数量
ema_volume = 150


def quant_stock(stock_number, stock_name, **kwargs):
    sdt = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) &
                      Q(date__lte=kwargs['date'])).order_by('-date')[:ema_volume]
    if len(sdt) < ema_volume-50:
        return
    if float(sdt[0].increase_rate.replace('%', '')) > 9:
        return

    trading_data = format_trading_data(sdt)
    df = calculate_macd(DataFrame(trading_data), kwargs['short_ema'], kwargs['long_ema'], kwargs['dif_ema'])
    df = calculate_kdj(df)
    today_analysis = df.iloc[-1]
    yestoday_analysis = df.iloc[-2]

    if today_analysis['macd'] > 0 and yestoday_analysis['macd'] > 0:
        if yestoday_analysis['k_d_dif'] < 0 < today_analysis['k_d_dif']:
            strategy_direction = 'long'
            strategy_name = 'macd_kdj_long'
            qr = QR(
                stock_number=stock_number, stock_name=stock_name, date=today_analysis.name,
                strategy_direction=strategy_direction, strategy_name=strategy_name,
                init_price=today_analysis['close_price']
            )

            if isinstance(qr, QR):
                if not check_duplicate_strategy(qr):
                    qr.save()


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据macd_kdj来选股')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算均线的日期')
    args = parser.parse_args()

    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y-%m-%d')
        except Exception, e:
            print 'Wrong date form'
            raise e
    else:
        qr_date = datetime.date.today()
    return qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    short_ema = 12
    long_ema = 26
    dif_ema = 9
    qr_date = setup_argparse()
    start_quant_analysis(short_ema=short_ema, long_ema=long_ema, dif_ema=dif_ema, date=qr_date,
                         quant_stock=quant_stock)
