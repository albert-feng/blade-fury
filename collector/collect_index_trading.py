#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用来获取股票指数每天的交易数据
"""

import json
import logging
import datetime

import requests
from mongoengine import Q

from config import market_index
from logger import setup_logging
from models import IndexDailyTrading as IDT
from models import StockDailyTrading as SDT


timeout = 60


def request_data(url):
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
        data = json.loads(r.text.replace('var js=', '').replace('quotation','\"quotation\"'))
    except Exception as e:
        logging.error('Error when loads market index data:' + str(e))
        raise e

    return data['quotation']


def save_index_data(idt):
    if isinstance(idt, IDT):
        today = datetime.date.today()
        sdt = SDT.objects(date=today)
        if not sdt:
            return

        exists_data = IDT.objects(Q(date=today) & Q(index_number=idt.index_number))
        if exists_data:
            return

        try:
            idt.save()
        except Exception as e:
            logging.error('Error when save market index data:' + str(e))


def collect_index_trading():
    index_data = request_data(market_index)
    for i in index_data:
        item_li = i.split(',')
        idt = IDT()
        idt.index_number = item_li[1]
        idt.index_name = item_li[2]
        idt.yesterday_closed_point = float(item_li[3])
        idt.today_opening_point = float(item_li[4])
        idt.today_closing_point = float(item_li[5])
        idt.today_highest_point = float(item_li[6])
        idt.today_lowest_point = float(item_li[7])
        idt.turnover_amount = int(item_li[8])
        idt.turnover_volume = int(item_li[9])
        idt.increase_point = float(item_li[10])
        idt.increase_rate = item_li[11]

        save_index_data(idt)


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    collect_index_trading()
