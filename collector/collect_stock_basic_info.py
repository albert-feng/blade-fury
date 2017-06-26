#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
这个脚本仅用来获取股票最基本的信息，名称和编号
"""

import json
import logging
import datetime

import requests

from config import eastmoney_stock_api
from models import StockInfo
from logger import setup_logging

timeout = 60


def request_and_handle_data(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Host': 'hqdigi2.eastmoney.com',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36'
    }

    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.encoding = 'utf-8'
    except Exception as e:
        logging.error('Request url %s failed: %s' % (url, e))
        raise e

    try:
        data = json.loads(r.text.replace('var js=', '').replace('rank', '\"rank\"').replace('pages', '\"pages\"'))
    except Exception as e:
        logging.error('Handle data failed:' + str(e))
        raise e

    return data


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
        stock_info = StockInfo(stock_number=stock_number, stock_name=stock_name, update_time=datetime.datetime.now())

        if not check_duplicate(stock_info):
            try:
                stock_info.save()
            except Exception as e:
                logging.error('Saving %s data failed:' % (stock_info.stock_number, e))


def check_duplicate(stock_info):
    """
    检查存储的数据是否重复
    """
    try:
        cursor = StockInfo.objects(stock_number=stock_info.stock_number)
    except Exception as e:
        logging.error('Query %s data failed: %s' % (stock_info.stock_number, e))
        raise e
    if cursor:
        return True

    return False

if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock basic info')
    collect_stock_info()
    logging.info('Collect stock basic info Success')
