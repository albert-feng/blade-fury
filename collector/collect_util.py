# -*- coding: utf-8 -*-
"""
# Created On 2024/11/12 下午10:59
---------
@summary: 
---------
@author: fengweigang
@email: fwg1989@gmail.com
"""

from datetime import date

from pandas import DataFrame

from collector.tushare_util import get_pro_client
from config import exchange_market


def estimate_market(stock_number, attr='code') -> str:
    market = ''
    for i in exchange_market:
        if stock_number[0] in i.get('pattern'):
            market = i.get(attr)
            break

    if not market:
        raise Exception('Wrong stock number %s' % stock_number)
    return market


def get_tushare_month_trading(stock_number, start_date=None, end_date=None, ):
    ts_code = stock_number + '.' + estimate_market(stock_number, attr='market').upper()
    if isinstance(start_date, date):
        start_date = start_date.strftime('%Y%m%d')
    if isinstance(end_date, date):
        end_date = end_date.strftime('%Y%m%d')

    month_trade_data: DataFrame = get_pro_client().monthly(ts_code=ts_code, start_date=start_date, end_date=end_date,
        fields='ts_code,trade_date,open,high,low,close,vol,amount')
    return month_trade_data
