#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
获取股票研究报告数据
"""


import random
import time
import datetime
import logging

import requests
from bs4 import BeautifulSoup

from models import StockInfo
from config import company_report
from logger import setup_logging


timeout = 30  # 发送http请求时的超时时间
page = 20  # 每次查询数据库的步长，以防出现cursor超时的错误


def send_request(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Connection': 'keep-alive',
        'Host': 'data.eastmoney.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36',
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    html = r.text
    if not html:
        logging.warning('No data when request this url:' + url)
    return html


def collect_company_report():
    report_list = requests.get(company_report).json().get('data', [])

    for r in report_list:
        stock_number = r.get('secuFullCode', '').strip().split('.')[0]
        stock_name = r.get('secuName', '').strip()
        date = datetime.datetime.strptime(r.get('datetime').split('T')[0], '%Y-%m-%d')
        title = r.get('title')
        author = r.get('author')
        rate_change = r.get('change')
        rate = r.get('rate')
        institution = r.get('insName')

        content_url = 'http://data.eastmoney.com/report/' + date.strftime('%Y%m%d') + '/' + r.get('infoCode') + '.html'
        content = BeautifulSoup(send_request(content_url), 'lxml').find('div', class_='newsContent').text


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock detail info')
    collect_company_report()
    logging.info('Collect stock detail info Success')
