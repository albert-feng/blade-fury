#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime
import time
import random

import requests
from bs4 import BeautifulSoup
from mongoengine import Q

from logger import setup_logging
from config import history_trading
from models import StockInfo, StockDailyTrading as SDT


timeout = 30


def send_request(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Connection': 'keep-alive',
        'Host': 'soft-f9.eastmoney.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36',
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    html = r.text

    if not html:
        logging.warning('No data when request this url:' + url)
    return html


def check_exists(stock_number, date):
    cursor = SDT.objects(Q(stock_number=stock_number) & Q(date=date))
    if cursor:
        return True
    else:
        return False


def collect_his_trading(stock_number, stock_name):
    if stock_number.startswith('6'):
        req_url = history_trading.format(stock_number+'01')
    else:
        req_url = history_trading.format(stock_number+'02')
    his_html = send_request(req_url)

    his_soup = BeautifulSoup(his_html, 'lxml')
    his_table = his_soup.find('table', id='tablefont')

    if his_table:
        his_data = his_table.find_all('tr')[1:]
        for i in his_data:
            date = datetime.datetime.strptime(i.find('p', class_='date').text, '%Y-%m-%d')
            today_opening_price = float(i.find_all('td')[1].text.replace('&nbsp', '').strip())
            today_highest_price = float(i.find_all('td')[2].text.replace('&nbsp', '').strip())
            today_lowest_price = float(i.find_all('td')[3].text.replace('&nbsp', '').strip())
            today_closing_price = float(i.find_all('td')[4].text.replace('&nbsp', '').strip())
            increase_rate = i.find_all('td')[5].text.replace('&nbsp', '').strip() + '%'
            increase_amount = float(i.find_all('td')[6].text.replace('&nbsp', '').strip())
            turnover_rate = i.find_all('td')[7].text.replace('&nbsp', '').strip() + '%'

            if float(increase_rate.replace('%', '')) != 0.0 and float(turnover_rate.replace('%', '')) != 0.0:
                # 去掉停牌期间的行情数据
                if not check_exists(stock_number, date):
                    sdt = SDT(stock_number=stock_number, stock_name=stock_name, date=date,
                              today_opening_price=today_opening_price, today_highest_price=today_highest_price,
                              today_lowest_price=today_lowest_price, today_closing_price=today_closing_price,
                              increase_rate=increase_rate, increase_amount=increase_amount, turnover_rate=turnover_rate)
                    sdt.save()


def begin_collect_his():
    stock_info = StockInfo.objects()

    for i in stock_info:
        try:
            collect_his_trading(i.stock_number, i.stock_name)
        except Exception, e:
            logging.error('Collect %s his data failed:%s' % (i.stock_number, e))
        finally:
            time.sleep(random.random())


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start collect history trading data')
    begin_collect_his()
    logging.info('Collect history trading data success')
