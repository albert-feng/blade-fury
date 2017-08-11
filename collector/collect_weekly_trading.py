#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import datetime
import json
import argparse

from mongoengine import Q

from models import StockWeeklyTrading as SWT
from models import StockInfo
from config import stock_exchange, datayes_week_trading
from config import datayes_headers
from collector.collect_data_util import send_request
from logger import setup_logging
from collector.collect_data_util import check_duplicate


query_step = 100


def start_collect_data(start_date, end_date):

    try:
        all_stocks = StockInfo.objects()
    except Exception as e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    stocks_count = all_stocks.count()
    skip = 0

    while skip < stocks_count:
        try:
            stocks = StockInfo.objects().skip(skip).limit(query_step)
        except Exception as e:
            logging.error('Error when query skip %s  StockInfo:%s' % (skip, e))
            stocks = []

        for i in stocks:
            try:
                collect_stock_data(i.stock_number, start_date, end_date)
            except Exception as e:
                logging.error('Error when collect datayes weekly trading data %s: %s' % (i.stock_number, e))
        skip += query_step


def collect_stock_data(stock_number, start_date, end_date):
    if not isinstance(start_date, datetime.date) or not isinstance(end_date, datetime.date):
        return

    sec_id = ''
    if stock_number.startswith('60'):
        sec_id = stock_number + '.' + stock_exchange.get(u'上海')
    elif stock_number.startswith('00') or stock_number.startswith('30'):
        sec_id = stock_number + '.' + stock_exchange.get(u'深圳')

    if not sec_id:
        return

    url = datayes_week_trading.format(sec_id, start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
    res_data = json.loads(send_request(url, datayes_headers))
    if res_data.get('retCode', 0) != 1:
        return

    trading_data = res_data.get('data', [])
    for i in trading_data:
        if i.get('numDays', 0) == 0:
            continue

        stock_number = i.get('ticker')
        try:
            first_trade_date = datetime.datetime.strptime(i.get('firstTradeDate'), '%Y-%m-%d %H:%M:%S')
            last_trade_date = datetime.datetime.strptime(i.get('lastTradeDate'), '%Y-%m-%d %H:%M:%S')
            end_date = datetime.datetime.strptime(i.get('endDate'), '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logging.error('Format time failed:' + str(e))
            continue

        former_swt = SWT.objects(Q(stock_number=stock_number) & Q(first_trade_date=first_trade_date))
        new_object = True
        if former_swt:
            swt = former_swt.next()
            if swt.last_trade_date >= last_trade_date:
                continue
            new_object = False
        else:
            swt = SWT()
            swt.stock_number = stock_number
            swt.stock_name = i.get('secShortName')

        swt.trade_days = int(i.get('numDays'))
        swt.first_trade_date = first_trade_date
        swt.last_trade_date = last_trade_date
        swt.end_date = end_date
        swt.pre_close_price = float(i.get('preClosePrice'))
        swt.weekly_open_price = float(i.get('openPrice'))
        swt.weekly_close_price = float(i.get('closePrice'))
        swt.weekly_highest_price = float(i.get('highestPrice'))
        swt.weekly_lowest_price = float(i.get('lowestPrice'))
        swt.ad_open_price = float(i.get('adOpenPrice'))
        swt.ad_close_price = float(i.get('adClosePrice'))
        swt.ad_highest_price = float(i.get('adHighestPrice'))
        swt.ad_lowest_price = float(i.get('adLowestPrice'))
        swt.range_percent = str(i.get('rangePct')) + '%'
        swt.increase_rate = str(i.get('adChgPct')) + '%'
        swt.turnover_amount = int(i.get('turnoverValue')) / 10000
        swt.turnover_volume = int(i.get('turnoverVol')) / 100

        if new_object:
            if not check_duplicate(swt):
                swt.save()
        else:
            swt.save()


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'采集周线数据')
    parser.add_argument(u'-s', action=u'store', dest='start_date', required=False, help=u'起始时间')
    parser.add_argument(u'-e', action=u'store', dest='end_date', required=False, help=u'结束时间')

    args = parser.parse_args()
    if args.start_date and args.end_date:
        try:
            start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(args.end_date, '%Y-%m-%d').date()
        except Exception as e:
            print('Wrong date form')
            raise e
    else:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=30)

    return start_date, end_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    start_date, end_date = setup_argparse()
    start_collect_data(start_date, end_date)
