#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'fengweigang'


import json
import logging
import datetime

import requests

from config import eastmoney_stock_api
from models import StockDailyTrading as SDT
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
    except Exception, e:
        logging.error('Request url %s failed: %s' % (url, e))
        raise e

    try:
        data = json.loads(r.text.replace('var js=', '').replace('rank', '\"rank\"').replace('pages', '\"pages\"'))
    except Exception, e:
        logging.error('Handle data failed:' + str(e))
        raise e

    return data


def collect_stock_daily_trading():
    """
    获取每日股票交易数据
    """
    url = eastmoney_stock_api
    data = request_and_handle_data(url)

    stock_data = data['rank']
    for i in stock_data:
        stock = i.split(',')
        stock_number = stock[1]
        stock_name = stock[2]
        sdt = SDT(stock_number=stock_number, stock_name=stock_name)
        sdt.yesterday_closed_price = float(stock[3])
        sdt.today_opening_price = float(stock[4])
        sdt.today_closing_price = float(stock[5])
        sdt.today_highest_price = float(stock[6])
        sdt.today_lowest_price = float(stock[7])
        sdt.turnover_amount = int(stock[8])
        sdt.turnover_volume = int(stock[9])
        sdt.increase_amount = float(stock[10])
        sdt.increase_rate = stock[11]
        sdt.today_average_price = float(stock[12])
        sdt.quantity_relative_ratio = float(stock[22])
        sdt.turnover_rate = stock[23]
        sdt.save()


def is_weekend():
    """
    排除掉周六和周日这两个不交易的日子
    """
    weekday = datetime.datetime.today().weekday()
    if weekday in [5, 6]:
        logging.warning('Stock will not trade on weekend')
        return True
    else:
        return False


if __name__ == '__main__':
    setup_logging(__file__)
    if not is_weekend():
        logging.info('Start Collect %s Trading Data' % datetime.date.today())
        collect_stock_daily_trading()
        logging.info('Collect %s Trading Data Success' % datetime.date.today())
