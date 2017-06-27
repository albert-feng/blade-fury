#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用来获取股票公告，数据来自东财，获取最新的25个公告，如果又新的公告出来，之前的也不会删除
"""

import random
import time
import datetime
import logging
import json
import chardet

import requests
from bs4 import BeautifulSoup
from mongoengine import Q

from models import StockInfo, StockNotice
from config import eastmoney_data, company_notice, single_notice
from logger import setup_logging


timeout = 30  # 发送http请求的超时时间
query_step = 30  # 一次从数据库中取出的数据量


def send_request(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        # 'Host': 'data.eastmoney.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36',
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    #r.encoding = 'utf-8'
    html = r.text
    if not html:
        logging.warning('No data when request this url:' + url)
    return html


def is_exists(notice_code):
    cursor = StockNotice.objects(code=notice_code)

    if cursor:
        return True
    else:
        return False


def collect_notice(stock_info):
    req_url = company_notice.format(stock_info.stock_number)
    raw_data = send_request(req_url).replace('var', '').replace('=', '').replace(';', '').strip()
    notice_data = json.loads(raw_data).get('data', [])

    for n in notice_data:
        notice_title = n.get('NOTICETITLE')
        notice_code = n.get('INFOCODE')
        notice_date = datetime.datetime.strptime(n.get('NOTICEDATE').split('T')[0], '%Y-%m-%d')
        notice_url = single_notice.format(stock_info.stock_number, notice_code)

        if not is_exists(notice_code):
            stock_notice = StockNotice(title=notice_title, code=notice_code, date=notice_date,
                content_url=notice_url, stock_number=stock_info.stock_number, stock_name=stock_info.stock_name)
            stock_notice.save()


def start_collect_notice():
    try:
        all_stocks = StockInfo.objects()
    except Exception, e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    stocks_count = len(all_stocks)
    skip = 0

    while skip < stocks_count:
        try:
            stocks = StockInfo.objects().skip(skip).limit(query_step)
        except Exception, e:
            logging.error('Error when query skip %s  StockInfo:%s' % (skip, e))
            stocks = []

        for i in stocks:
            try:
                collect_notice(i)
            except Exception, e:
                logging.error('Error when collect %s notice: %s' % (i.stock_number, e))
            # time.sleep(random.random())
        skip += query_step
        # time.sleep(random.random()*10)


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock detail info')
    start_collect_notice()
    logging.info('Collect stock detail info Success')
