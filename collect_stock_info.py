#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'fengweigang'

import json
import datetime

import requests

from config import eastmoney_stock_api
from models import StockInfo

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
    r = requests.get(url, headers=headers, timeout=timeout)
    data = json.loads(r.text.replace('var js=', '').replace('rank', '\"rank\"').replace('pages', '\"pages\"'))
    return data

def collect_stock_info():
    url = eastmoney_stock_api
    data = request_and_handle_data(url)

    stock_data = data['rank']
    for i in stock_data:
        stock = i.split(',')
        stock_number = stock[1]
        stock_name = stock[2]
        stock_info = StockInfo()
        stock_info.stock_number = stock_number
        stock_info.stock_name = stock_name
        stock_info.save()


if __name__ == '__main__':

    collect_stock_info()
