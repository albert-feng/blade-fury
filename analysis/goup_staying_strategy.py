#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'albert feng'


import datetime
import logging
import argparse

from mongoengine import Q

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import check_duplicate_strategy
from analysis.technical_analysis_util import start_quant_analysis, pre_sdt_check


quant_count = 40
goup_stay = 9.5


def quant_stock(stock_number, stock_name, **kwargs):
    qr_date = kwargs['qr_date']
    week_long = kwargs.get('week_long', False)
    if not pre_sdt_check(stock_number, **kwargs):
        return

    strategy_name = 'goup_staying'
    if week_long:
        strategy_name = 'weeklong_' + strategy_name

    sdt = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) &
                      Q(date__lte=qr_date)).order_by('-date')[:quant_count]
    if len(sdt) < quant_count:
        return

    if float(sdt[0].increase_rate.replace('%', '').strip()) > goup_stay:
        # 日线：当日成交额（单位千）换算为“亿”并保留两位小数
        day_turnover_raw = sdt[0].turnover_amount
        turnover_amount_str = f"{day_turnover_raw / 10000:.2f}亿"
        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=qr_date,
            strategy_direction='long', strategy_name=strategy_name,
            init_price=sdt[0].today_closing_price, industry_involved=kwargs.get('industry_involved'),
            increase_rate=float(sdt[0].increase_rate.replace('%', '').strip()),
            turnover_amount=turnover_amount_str
        )
        if not check_duplicate_strategy(qr):
            qr.save()
            return qr


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据长短均线的金叉来选股')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算均线的日期')
    parser.add_argument(u'-r', action=u'store_true', dest='real_time', required=False, help=u'是否实时计算')
    parser.add_argument(u'-w', action=u'store_true', dest='week_long', required=False, help=u'是否处于周线多头')

    args = parser.parse_args()
    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y-%m-%d')
        except Exception as e:
            print('Wrong date form')
            raise e
    else:
        qr_date = datetime.date.today()

    return qr_date, args.week_long


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    qr_date, week_long = setup_argparse()
    today_trading = {}

    real_time_res = start_quant_analysis(qr_date=qr_date, quant_stock=quant_stock, today_trading=today_trading,
                                         week_long=week_long)
