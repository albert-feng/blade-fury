# -*- coding: utf-8 -*-
"""
# Created On 2024/11/22 下午8:12
---------
@summary: 
---------
@author: fengweigang
@email: fwg1989@gmail.com
"""


import datetime
import logging
import argparse

from mongoengine import Q

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import check_duplicate_strategy
from analysis.technical_analysis_util import start_quant_analysis, pre_sdt_check


quant_count = 10
goup_stay = 9.5


def quant_stock(stock_number, stock_name, **kwargs):
    qr_date = kwargs['qr_date']
    strategy_name = 'potential'
    if stock_number.startswith('688') or stock_number.startswith('30'):  # 过滤掉可以涨20%的票
        return

    sdt = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) &
                      Q(date__lte=qr_date)).order_by('-date')[:quant_count]
    if len(sdt) < quant_count:
        return

    # 过滤出前一天涨停然后转弱的票
    if (float(sdt[1].increase_rate.replace('%', '').strip()) > goup_stay >
            float(sdt[0].increase_rate.replace('%', '').strip()) and
            float(sdt[2].increase_rate.replace('%', '').strip()) < goup_stay):
        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=qr_date,
            strategy_direction='long', strategy_name=strategy_name,
            init_price=sdt[0].today_closing_price, industry_involved=kwargs.get('industry_involved'),
            increase_rate=float(sdt[0].increase_rate.replace('%', '').strip())
        )
        if not check_duplicate_strategy(qr):
            qr.save()
            return qr


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据弱转强策略')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算的日期')

    args = parser.parse_args()
    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y-%m-%d')
        except Exception as e:
            print('Wrong date form')
            raise e
    else:
        qr_date = datetime.date.today()

    return qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    qr_date = setup_argparse()

    real_time_res = start_quant_analysis(qr_date=qr_date, quant_stock=quant_stock)