#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import argparse

from mongoengine import Q
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import calculate_macd, format_trading_data, check_duplicate_strategy
from analysis.technical_analysis_util import start_quant_analysis, collect_stock_daily_trading, display_quant
from analysis.technical_analysis_util import pre_sdt_check, setup_realtime_sdt


step = 100  # 一次从数据库取出打股票数量
ema_volume = 150
year_num = 250


def quant_stock(stock_number, stock_name, **kwargs):
    if not pre_sdt_check(stock_number, kwargs['qr_date']):
        return

    real_time = kwargs.get('real_time', False)
    sdt = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) &
                      Q(date__lte=kwargs['qr_date'])).order_by('-date')[:ema_volume]

    if float(sdt[0].increase_rate.replace('%', '')) > 9:
        return ''

    if real_time:
        sdt = setup_realtime_sdt(stock_number, sdt, kwargs)
    trading_data = format_trading_data(sdt)
    df = calculate_macd(DataFrame(trading_data), kwargs['short_ema'], kwargs['long_ema'], kwargs['dif_ema'])
    today = df.iloc[-1]
    yestoday = df.iloc[-2]

    strategy_direction = ''
    if yestoday['macd'] < 0 < today['macd']:
        strategy_direction = 'long'
    elif yestoday['macd'] > 0 > today['macd']:
        strategy_direction = 'short'

    if strategy_direction:
        strategy_name = 'macd_%s_%s_%s_%s' % (strategy_direction, kwargs['short_ema'], kwargs['long_ema'],
                                              kwargs['dif_ema'])
        increase_rate = round((today['close_price'] - yestoday['close_price']) / yestoday['close_price'], 4) * 100
        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=today.name,
            strategy_direction=strategy_direction, strategy_name=strategy_name, init_price=today['close_price'],
            industry_involved=kwargs.get('industry_involved'), increase_rate=increase_rate
        )
        if real_time and strategy_direction == 'long':
            return qr
        if not real_time and not check_duplicate_strategy(qr):
            qr.save()
            return qr
    return ''


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据长短均线的金叉来选股')
    parser.add_argument(u'-s', action=u'store', dest='short_ema', required=True, help=u'短期指数加权均线数')
    parser.add_argument(u'-l', action=u'store', dest='long_ema', required=True, help=u'长期指数加权均线数')
    parser.add_argument(u'-d', action=u'store', dest='dif_ema', required=True, help=u'dif指数加权均线数')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算策略的日期')
    parser.add_argument(u'-r', action=u'store_true', dest='real_time', required=False, help=u'是否实时计算')

    args = parser.parse_args()
    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y-%m-%d')
        except Exception as e:
            print('Wrong date form')
            raise e
    else:
        qr_date = datetime.date.today()

    return int(args.short_ema), int(args.long_ema), int(args.dif_ema), qr_date, args.real_time


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    short_ema, long_ema, dif_ema, qr_date, real_time = setup_argparse()
    today_trading = {}
    if real_time:
        today_trading = collect_stock_daily_trading()

    real_time_res = start_quant_analysis(short_ema=short_ema, long_ema=long_ema, dif_ema=dif_ema, qr_date=qr_date,
                                         quant_stock=quant_stock, real_time=real_time, today_trading=today_trading)
    if real_time_res and real_time:
        display_quant(real_time_res)
