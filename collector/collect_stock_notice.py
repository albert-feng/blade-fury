#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用来获取股票公告，数据来自东财，获取最新的25个公告，如果又新的公告出来，之前的也不会删除
"""

import random
import time
import datetime
import logging

import requests
from bs4 import BeautifulSoup
from mongoengine import Q

from models import StockInfo, StockNotice
from config import company_accouncement, eastmoney_data
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
        'Host': 'data.eastmoney.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36',
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    html = r.text
    if not html:
        logging.warning('No data when request this url:' + url)
    return html


def check_duplicate(notice_title, notice_cate, notice_date):
    cursor = StockNotice.objects(Q(notice_title=notice_title) &
                                 Q(notice_cate=notice_cate) &
                                 Q(notice_date=notice_date))

    if cursor:
        return True
    else:
        return False


def collect_notice(stock_info):
    req_url = company_accouncement.format(stock_info.stock_number)
    notice_list_html = send_request(req_url)
    notice_list_soup = BeautifulSoup(notice_list_html, 'lxml')

    if not notice_list_soup or not notice_list_soup.find('div', class_='snBox'):
        return

    notice_list = notice_list_soup.find('div', class_='snBox').find('div', class_='cont').find_all('li')
    for i in notice_list:
        notice_title = i.find('span', class_='title').find('a').text
        notice_cate = i.find('span', class_='cate').text
        notice_date_str = i.find('span', class_='date').text
        notice_date = datetime.datetime.strptime(notice_date_str, '%Y-%m-%d')
        notice_url = eastmoney_data + i.find('a').get('href')

        if not check_duplicate(notice_title, notice_cate, notice_date):
            notice_html = send_request(notice_url)
            notice_soup = BeautifulSoup(notice_html, 'lxml')
            notice_content = ''
            if notice_soup:
                notice_content = notice_soup.find('pre').text.strip()

            stock_notice = StockNotice(stock_number=stock_info.stock_number, stock_name=stock_info.stock_name,
                                       notice_title=notice_title, notice_cate=notice_cate, notice_date=notice_date,
                                       notice_url=notice_url, notice_content=notice_content)
            stock_notice.save()
            time.sleep(random.random())


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
            time.sleep(random.random())
        skip += query_step
        time.sleep(random.random()*10)


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock detail info')
    start_collect_notice()
    logging.info('Collect stock detail info Success')
