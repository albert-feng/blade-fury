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
from collector.collect_data_util import request_and_handle_data


retry = 5


def collect_stock_daily_trading():
    """
    获取并保存每日股票交易数据
    """
    url = eastmoney_stock_api
    data = {}
    global retry
    while retry > 0:
        try:
            data = request_and_handle_data(url)
            retry = 0
        except Exception:
            retry -= 1

    stock_data = data.get('rank', [])
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
        quantity_relative_ratio = 0 if stock[22] == '-' else stock[22]
        sdt.quantity_relative_ratio = float(quantity_relative_ratio)
        sdt.turnover_rate = stock[23]

        if float(sdt.turnover_rate.replace('%', '')) == 0.0:
            # 去掉停牌的交易数据
            continue

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
            check_item = ['today_opening_price', 'today_closing_price', 'today_highest_price', 'today_lowest_price',
                          'increase_amount', 'increase_rate', 'turnover_rate']
            for i in check_item:
                if sdt[i] != latest_sdt[i]:
                    return False
            logging.info('%s trading data is same with latest STD, this data will not be saved.' % sdt.stock_number)
            return True
        else:
            return False


def main():
    setup_logging(__file__, logging.WARNING)
    if not is_weekend():
        logging.info('Start Collect %s Trading Data' % datetime.date.today())
        collect_stock_daily_trading()
        logging.info('Collect %s Trading Data Success' % datetime.date.today())


if __name__ == '__main__':
    main()
