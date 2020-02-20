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
from collector.collect_data_util import request_and_handle_data


def collect_stock_info():
    """
    存储股票最基本的信息
    """
    url = eastmoney_stock_api
    data = request_and_handle_data(url)

    stock_data = data['rank']
    for i in stock_data:
        stock = i.split(',')
        stock_number = stock[1]
        stock_name = stock[2]
        total_value = 0 if stock[-2] == '-' else stock[-2]

        cursor = StockInfo.objects(stock_number=stock_number)
        if cursor:
            stock_info = cursor[0]
            stock_info.total_value = int(total_value)
            stock_info.update_time = datetime.datetime.now()
        else:
            stock_info = StockInfo(stock_number=stock_number, stock_name=stock_name,
                                   update_time=datetime.datetime.now(), total_value=int(total_value))

        try:
            stock_info.save()
        except Exception as e:
            logging.error('Saving %s data failed: %s' % (stock_info.stock_number, e))


def check_duplicate(stock_info):
    """
    检查存储的数据是否重复
    """
    try:
        cursor = StockInfo.objects(stock_number=stock_info.stock_number)
        if cursor:
            data = cursor.next()
            if data.stock_name != stock_info.stock_name:
                data.stock_name = stock_info.stock_name
                data.save()
            return True
    except Exception as e:
        logging.error('Query %s data failed: %s' % (stock_info.stock_number, e))
        raise e

    return False


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock basic info')
    collect_stock_info()
    logging.info('Collect stock basic info Success')
