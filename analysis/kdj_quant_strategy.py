# -*- coding: utf-8 -*-
"""
# Created On 2024/12/6 上午10:40
---------
@summary: 计算kdj指标选股
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
from analysis.technical_analysis_util import *


quant_count = 200


def quant_stock(stock_number, stock_name, **kwargs):
    # 获取查询日期
    qr_date = kwargs['qr_date']
    n = kwargs['n']
    k = kwargs['k']
    d = kwargs['d']
    strategy_direction = 'long'

    if not pre_sdt_check(stock_number, **kwargs):
        return

    strategy_name = 'kdj_long_%s_%s_%s' % (n, k, d)
    sdt = SDT.objects(Q(stock_number=stock_number) & Q(date__lte=qr_date)).order_by('-date')[:quant_count]

    if len(sdt) < quant_count:
        # trading data not enough
        return
    trading_data = format_trading_data(sdt)
    df = calculate_kdj(DataFrame(trading_data), n, k, d)
    today = df.iloc[-1]
    yestoday = df.iloc[-2]

    if yestoday['j'] < yestoday['d'] and today['j'] > today['d']:
        increase_rate = round((today['close_price'] - yestoday['close_price']) / yestoday['close_price'], 4) * 100
        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=today.name,
            strategy_direction=strategy_direction, strategy_name=strategy_name, init_price=today['close_price'],
            industry_involved=kwargs.get('industry_involved'), increase_rate=increase_rate
        )
        if not check_duplicate_strategy(qr):
            qr.save()
            return qr

    return None


def setup_argparse() -> (datetime.date, int, int, int):
    parser = argparse.ArgumentParser(description=u'计算KDJ指标')
    parser.add_argument(u'-n', action=u'store', dest='n', required=True, help=u'RSV周期')
    parser.add_argument(u'-k', action=u'store', dest='k', required=True, help=u'K平滑周期')
    parser.add_argument(u'-d', action=u'store', dest='d', required=True, help=u'D平滑周期')
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

    return qr_date, int(args.n), int(args.k), int(args.d)


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    qr_date, n, k, d = setup_argparse()

    real_time_res = start_quant_analysis(qr_date=qr_date, quant_stock=quant_stock, n=n, k=k, d=d)
