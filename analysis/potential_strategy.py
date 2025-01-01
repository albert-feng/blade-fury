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
from analysis.technical_analysis_util import start_quant_analysis, calculate_highest_rate


quant_count = 10
goup_stay = 9.5


def quant_stock(stock_number, stock_name, **kwargs):
    """
    量化选股函数

    该函数根据给定的股票代码和名称，以及额外的关键字参数，执行一系列条件判断来决定是否将该股票添加到数据库中
    条件包括股票代码的前缀、历史价格表现、以及是否满足特定的量化策略

    参数:
    - stock_number (str): 股票代码
    - stock_name (str): 股票名称
    - **kwargs: 额外的关键字参数，必须包含 'qr_date'，可选地包含 'industry_involved'

    返回:
    - QR: 如果股票满足条件，则返回保存在数据库中的QR对象，否则返回None
    """
    # 获取查询日期
    qr_date = kwargs['qr_date']
    # 定义策略名称
    strategy_name = 'potential'

    # 过滤掉北交所和科创板
    if (stock_number.startswith('688') or stock_number.startswith('9') or stock_number.startswith('8')
            or stock_number.startswith('4')):
        return

    # 查询股票数据
    sdt = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) &
                      Q(date__lte=qr_date)).order_by('-date')[:quant_count]
    # 如果查询结果不足quant_count条，直接返回
    if len(sdt) < quant_count:
        return

    # 过滤出前一天涨停然后转弱或者当天烂板的票
    if (calculate_highest_rate(sdt[1]) > goup_stay >
            float(sdt[0].increase_rate.replace('%', '').strip())) or (calculate_highest_rate(sdt[0]) > goup_stay and
            sdt[0].today_closing_price < sdt[0].today_highest_price):
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