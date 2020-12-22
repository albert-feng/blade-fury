#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import time

from bs4 import BeautifulSoup

from models import StockInfo
from logger import setup_logging
from collector.collect_data_util import send_request


query_step = 100
share_holder_url = {
    'http://soft-f9.eastmoney.com/soft/gp50.php?code=': True,
    'http://soft-f9.eastmoney.com/soft/gp51.php?code=': False,
}


def collect_share_holder(stockinfo):
    stock_number = stockinfo.stock_number
    stock_name = stockinfo.stock_name
    print(stock_number)
    if stock_number.startswith('6'):
        req_code = stock_number + '01'
    else:
        req_code = stock_number + '02'

    for k, v in share_holder_url.items():
        print(k, v)
        req_url = k + req_code
        share_html = send_request(req_url)
        share_soup = BeautifulSoup(share_html, 'lxml')
        share_table = share_soup.find('table', id='tablefont')

        for i in share_table.find_all('tr'):
            items = i.find_all('td')
            print(items)
            if items[0].text.startswith('20'):
                print(i)


def start_collect_holder():
    try:
        all_stocks = StockInfo.objects()
    except Exception as e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    stocks_count = len(all_stocks)
    skip = 0

    while skip < stocks_count:
        try:
            stocks = StockInfo.objects().skip(skip).limit(query_step)
        except Exception as e:
            logging.error('Error when query skip %s  StockInfo:%s' % (skip, e))
            stocks = []

        for i in stocks:
            try:
                start_collect_holder(i)
            except Exception as e:
                logging.error('Error when collect %s data: %s' % (i.stock_number, e))
            time.sleep(random.random())
        skip += query_step


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock detail info')
    start_collect_holder()
    logging.info('Collect stock detail info Success')