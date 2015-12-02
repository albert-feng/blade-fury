#!/usr/bin/env python
# -*- coding: utf-8 -*-


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


timeout = 30


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


def collect_notice(stock_number, stock_name):
    req_url = company_accouncement.format(stock_number)
    notice_list_html = send_request(req_url)
    notice_list_soup = BeautifulSoup(notice_list_html, 'lxml')

    notice_list = notice_list_soup.find('div', class_='cont').find_all('li')
    for i in notice_list:
        notice_title = i.find('span', class_='title').text
        notice_cate = i.find('span', class_='cate').text
        notice_date_str = i.find('span', class_='date').text
        notice_date = datetime.datetime.strptime(notice_date_str, '%Y-%m-%d')
        notice_url = eastmoney_data + i.find('a').get('href')

        if not check_duplicate(notice_title, notice_cate, notice_date):
            notice_html = send_request(notice_url)
            notice_soup = BeautifulSoup(notice_html, 'lxml')
            notice_content = notice_soup.find('pre').text

            stock_notice = StockNotice(stock_number=stock_number, stock_name=stock_name, notice_title=notice_title,
                                       notice_cate=notice_cate, notice_date=notice_date, notice_url=notice_url,
                                       notice_content=notice_content)
            stock_notice.save()
            time.sleep(random.random())


def main():
    setup_logging(__file__)

    try:
        all_stocks = StockInfo.objects().timeout(False)
    except Exception, e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    for i in all_stocks:
        try:
            collect_notice(i.stock_number, i.stock_name)
        except Exception, e:
            logging.error('Error when collect %s notice: %s' % (i.stock_number, e))


if __name__ == '__main__':
    main()
