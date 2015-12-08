#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用来获取一个股票每天的交易数据
"""

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
    获取并保存每日股票交易数据
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

        if not check_duplicate(sdt):
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


def check_duplicate(sdt):
    """
    检查某一天的交易数据是否与之前一天完全相同，如果完全相同，则不会保存这些交易数据
    为了规避一些法定假日不交易的情况，还有股票停牌的时候，停牌中的数据是不记录的
    """
    if isinstance(sdt, SDT):
        trading_date = SDT.objects(stock_number=sdt.stock_number).order_by('-date')
        if trading_date:
            latest_sdt = trading_date[0]
            check_item = ['yesterday_closed_price', 'today_opening_price', 'today_closing_price',
                          'today_highest_price', 'today_lowest_price', 'turnover_amount', 'turnover_volume',
                          'increase_amount', 'increase_rate', 'today_average_price', 'quantity_relative_ratio',
                          'turnover_rate']
            for i in check_item:
                if sdt[i] != latest_sdt[i]:
                    return False
            logging.warning('%s trading data is same with latest STD, this data will not be saved.' % sdt.stock_number)
            return True
        else:
            return False


def main():
    setup_logging(__file__)
    if not is_weekend():
        logging.info('Start Collect %s Trading Data' % datetime.date.today())
        collect_stock_daily_trading()
        logging.info('Collect %s Trading Data Success' % datetime.date.today())


if __name__ == '__main__':
    main()
