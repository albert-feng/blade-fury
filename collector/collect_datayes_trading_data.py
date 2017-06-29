#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import argparse

import requests
from mongoengine import Q

from config import datayes_headers, datayes_day_trading
from models import StockDailyTrading as SDT
from logger import setup_logging


def send_requests(url):
    headers = datayes_headers
    try:
        req = requests.get(url, headers=headers, timeout=60)
    except Exception, e:
        logging.error('Error when request %s:%s' % (url, e))
        raise e

    if not str(req.status_code).startswith('2'):
        raise Exception('Request datayes trading failed:%s' % req.status_code)
    return req.json()


def collect_datayes_data(date):
    url = datayes_day_trading.format(date.strftime('%Y%m%d'))
    datayes_data = send_requests(url)

    if datayes_data.get('retCode') != 1:
        return

    trading_data = datayes_data.get('data', [])
    for i in trading_data:
        is_open = i['isOpen']
        if is_open != 1:
            continue

        stock_number = i['ticker']
        stock_name = i['secShortName']
        yesterday_closed_price = i['actPreClosePrice']
        today_opening_price = i['openPrice']
        today_closing_price = i['closePrice']
        today_highest_price = i['highestPrice']
        today_lowest_price = i['lowestPrice']
        turnover_amount = int(i['turnoverValue']/10000)
        turnover_volume = int(i['turnoverVol']/100)
        increase_amount = i['closePrice'] - i['actPreClosePrice']
        increase_rate = str(round(increase_amount/i['actPreClosePrice'], 4) * 100) + '%'
        turnover_rate = str(i['turnoverRate'] * 100) + '%'
        total_stock = int(i['marketValue'] / i['closePrice'])
        circulation_stock = int(i['negMarketValue'] / i['closePrice'])
        date = datetime.datetime.strptime(i['tradeDate'], '%Y-%m-%d')

        sdt = SDT(stock_number=stock_number, stock_name=stock_name, yesterday_closed_price=yesterday_closed_price,
                  today_opening_price=today_opening_price, today_closing_price=today_closing_price,
                  today_highest_price=today_highest_price, today_lowest_price=today_lowest_price,
                  turnover_amount=turnover_amount, turnover_volume=turnover_volume, increase_amount=increase_amount,
                  increase_rate=increase_rate, turnover_rate=turnover_rate, total_stock=total_stock,
                  circulation_stock=circulation_stock, date=date)

        try:
            if not check_duplicate(sdt):
                sdt.save()
        except Exception, e:
            logging.error('Error when query or saving %s data:%s' % (sdt.stock_number, e))


def check_duplicate(sdt):
    if isinstance(sdt, SDT):
        cursor = SDT.objects(Q(stock_number=sdt.stock_number) & Q(date=sdt.date))
        if cursor:
            return True
        else:
            return False


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'采集datayes的股票日k数据，按时间倒序进行数据采集')
    parser.add_argument(u'-s', action=u'store', dest='start_date', required=True, help=u'开始采集的时间')
    parser.add_argument(u'-e', action=u'store', dest='end_date', required=True, help=u'结束采集的时间')
    args = parser.parse_args()

    start_date = args.start_date
    end_date = args.end_date

    try:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    except Exception, e:
        logging.error('Wrong date form:' + str(e))
        raise e

    return start_date, end_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    start_date, end_date = setup_argparse()

    delta = datetime.timedelta(1)
    collect_date = start_date
    while collect_date >= end_date:
        collect_datayes_data(collect_date)
        collect_date -= delta
