#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import datetime
import json
import argparse

from mongoengine import Q

from models import StockWeeklyTrading as SWT
from models import StockInfo
from config import datayes_week_ad
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

    end_date += datetime.timedelta(days=7)
    url = datayes_week_ad.format(stock_number, start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d'))
    res_data = json.loads(send_request(url, datayes_headers))
    if res_data.get('retCode', 0) != 1:
        return

    trading_data = res_data.get('data', [])
    for i in trading_data:
        trade_days = int(i.get('tradeDays'))
        if trade_days == 0:
            continue

        stock_number = i.get('ticker')
        try:
            first_trade_date = datetime.datetime.strptime(i.get('weekBeginDate'), '%Y-%m-%d')
            end_date = datetime.datetime.strptime(i.get('endDate'), '%Y-%m-%d')
            last_trade_date = datetime.datetime.strptime(i.get('endDate'), '%Y-%m-%d')
        except Exception as e:
            logging.error('Format time failed:' + str(e))
            continue

        former_swt = SWT.objects(Q(stock_number=stock_number) & Q(first_trade_date=first_trade_date))
        if len(former_swt):
            swt = former_swt[0]
            swt.trade_days = trade_days
            swt.first_trade_date = first_trade_date
            swt.last_trade_date = last_trade_date
            swt.end_date = end_date
            swt.ad_open_price = float(i.get('openPrice'))
            swt.ad_close_price = float(i.get('closePrice'))
            swt.ad_highest_price = float(i.get('highestPrice'))
            swt.ad_lowest_price = float(i.get('lowestPrice'))
        else:
            swt = SWT()
            swt.stock_number = stock_number
            swt.stock_name = i.get('secShortName')
            swt.trade_days = trade_days
            swt.first_trade_date = first_trade_date
            swt.last_trade_date = last_trade_date
            swt.end_date = end_date
            swt.pre_close_price = float(i.get('preClosePrice'))
            swt.ad_open_price = float(i.get('openPrice'))
            swt.ad_close_price = float(i.get('closePrice'))
            swt.ad_highest_price = float(i.get('highestPrice'))
            swt.ad_lowest_price = float(i.get('lowestPrice'))
            swt.increase_rate = str(round(i.get('chgPct') * 100, 2)) + '%'
            swt.turnover_amount = int(i.get('turnoverValue')) / 10000
            swt.turnover_volume = int(i.get('turnoverVol')) / 100

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
        start_date = end_date - datetime.timedelta(days=45)

    return start_date, end_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    start_date, end_date = setup_argparse()
    start_collect_data(start_date, end_date)
