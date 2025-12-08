#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'fengweigang'

import datetime
import argparse
import logging

from mongoengine import Q
from pandas import DataFrame

from analysis.technical_analysis_util import pre_swt_check, calculate_macd, check_duplicate_strategy
from analysis.technical_analysis_util import format_trading_data, start_quant_analysis, is_ad_price
from models import StockWeeklyTrading as SWT
from models import QuantResult as QR
from logger import setup_logging


def quant_stock(stock_number, stock_name, **kwargs):
    short_ema = kwargs['short_ema']
    long_ema = kwargs['long_ema']
    dif_ema = kwargs['dif_ema']
    qr_date = kwargs['qr_date']
    if not pre_swt_check(stock_number, **kwargs):
        return

    strategy_direction = 'long'
    strategy_name = 'dif_week_long_%s_%s_%s' % (short_ema, long_ema, dif_ema)
    quant_count = 250

    last_trade_date = qr_date + datetime.timedelta(days=7)
    swt = SWT.objects(Q(stock_number=stock_number) &
                      Q(last_trade_date__lte=last_trade_date)).order_by('-last_trade_date')[:quant_count]

    use_ad_price, swt = is_ad_price(stock_number, qr_date, swt)
    if not swt:
        return
    trading_data = format_trading_data(swt, use_ad_price)

    df = calculate_macd(DataFrame(trading_data), short_ema, long_ema, dif_ema)
    this_week = df.iloc[-1]
    last_week = df.iloc[-2]

    if last_week['dif'] < 0 < this_week['dif']:
        init_price = this_week['close_price']
        increase_rate = round((this_week['close_price'] - last_week['close_price']) / last_week['close_price'], 4) * 100
        # 周线：当周成交额（单位万）换算为“亿”并保留两位小数（按要求除以1000）
        week_turnover_raw = swt[0].turnover_amount
        turnover_amount_str = f"{week_turnover_raw / 1000:.2f}亿"

        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=qr_date,
            strategy_direction=strategy_direction, strategy_name=strategy_name, init_price=init_price,
            industry_involved=kwargs.get('industry_involved'), increase_rate=increase_rate,
            turnover_amount=turnover_amount_str
        )
        if not check_duplicate_strategy(qr):
            qr.save()


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据是否启动来选股')
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
