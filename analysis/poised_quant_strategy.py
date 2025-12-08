#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import argparse

from mongoengine import Q
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import calculate_macd, format_trading_data, calculate_ma, start_quant_analysis, \
    check_duplicate_strategy, pre_sdt_check


period = 3
ema_volume = 500
short_ma = 5
long_ma = 10
short_ema = 12
long_ema = 26
dif_ema = 9


def quant_stock(stock_number, stock_name, **kwargs):
    qr_date = kwargs['qr_date']
    if not pre_sdt_check(stock_number, **kwargs):
        return

    strategy_name = "poised_long_day"
    sdt = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) &
                      Q(date__lte=qr_date)).order_by('-date')[:ema_volume]
    trading_data = format_trading_data(sdt)
    df = calculate_ma(DataFrame(trading_data), short_ma, long_ma)
    df = calculate_macd(df, short_ema, long_ema, dif_ema)
    today = df.iloc[-1]
    yestoday = df.iloc[-2]

    if yestoday['close_price'] < yestoday['long_ma'] and today['close_price'] > today['short_ma'] \
       and today['close_price'] > today['long_ma']:

        short_point = -1
        for i in range(1, len(df)):
            if df.iloc[-i].diff_ma > 0:
                short_point = i
                break

        if short_point < period:
            return

        if df.iloc[-short_point:].dif.min() > 0:
            increase_rate = round((today['close_price'] - yestoday['close_price']) / yestoday['close_price'], 4) * 100
            # 日线：当日成交额（单位千）换算为“亿”并保留两位小数
            day_turnover_raw = sdt[0].turnover_amount
            turnover_amount_str = f"{day_turnover_raw / 10000:.2f}亿"

            qr = QR(
                stock_number=stock_number, stock_name=stock_name, date=today.name,
                strategy_direction='long', strategy_name=strategy_name,
                init_price=today['close_price'], industry_involved=kwargs.get('industry_involved'),
                increase_rate=increase_rate, turnover_amount=turnover_amount_str
            )

            if not check_duplicate_strategy(qr):
                qr.save()
                return qr


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据k线背离来选股')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算背离策略的日期')

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
