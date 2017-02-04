#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
获取股票研究报告数据
"""


import datetime
import logging

import requests
from bs4 import BeautifulSoup
from mongoengine import Q

from models import StockReport
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
    r.encoding = 'utf-8'
    html = r.text
    if not html:
        logging.warning('No data when request this url:' + url)
    return html


def check_duplicate(info_code, date):
    cursor = StockReport.objects(Q(info_code=info_code) & Q(date=date))
    if cursor:
        return True
    else:
        return False


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
        info_code = r.get('infoCode').strip()

        content_url = 'http://data.eastmoney.com/report/' + date.strftime('%Y%m%d') + '/' + info_code + '.html'
        try:
            content = BeautifulSoup(send_request(content_url), 'lxml').find('div', class_='newsContent').text.strip()
        except Exception, e:
            logging.error('Error when get %s report content:%s' % (stock_number, e))
            continue

        if not check_duplicate(info_code, date):
            stock_report = StockReport(stock_number=stock_number, stock_name=stock_name, date=date, title=title,
                                       author=author, rate_change=rate_change, rate=rate, institution=institution,
                                       info_code=info_code, content=content)
            try:
                stock_report.save()
            except Exception, e:
                logging.error('Error when save %s report %s:%s' % (stock_number, info_code, e))


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock detail info')
    collect_company_report()
    logging.info('Collect stock detail info Success')
