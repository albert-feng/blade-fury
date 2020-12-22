#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
这个脚本仅用来获取股票最基本的信息，名称和编号
"""

import logging
import datetime

from config import eastmoney_stock_api
from models import StockInfo
from logger import setup_logging
from collector.tushare_util import get_pro_client


def collect_stock_info():
    """
    存储股票最基本的信息
    """

    stock_data = get_pro_client().stock_basic(exchange='', list_status='L',
                                              fields='ts_code,symbol,name,area,industry,list_date')
    for i in range(len(stock_data)):
        stock = stock_data.iloc[i]
        cursor = StockInfo.objects(stock_number=stock.symbol)
        if cursor:
            stock_info = cursor[0]
        else:
            stock_info = StockInfo(stock_number=stock.symbol)

        stock_info.stock_name = stock['name']
        stock_info.area = stock.area
        stock_info.industry = stock.industry
        stock_info.list_date = stock.list_date

        try:
            stock_info.save()
        except Exception as e:
            logging.error("save base stock_info error, e = %s" % e)


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock basic info')
    collect_stock_info()
    logging.info('Collect stock basic info Success')
