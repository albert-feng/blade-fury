# -*- coding: utf-8 -*-
"""
# Created On 2024/11/12 下午10:36
---------
@summary: 
---------
@author: fengweigang
@email: fwg1989@gmail.com
"""


import logging
import datetime
import argparse

from mongoengine import Q

from logger import setup_logging
from models import StockInfo, StockMonthTrading as SMT
from collector.collect_util import get_tushare_month_trading


query_step = 100


def begin_collect_month_trading(start_date, end_date):

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
                collect_stock_month(i.stock_number, start_date, end_date)
            except Exception as e:
                logging.error('Error when collect datayes weekly trading data %s: %s' % (i.stock_number, e))
        skip += query_step


def collect_stock_month(stock_number, start_date, end_date):
    month_data = get_tushare_month_trading(stock_number, start_date, end_date)

    for i in range(0, len(month_data)):
        trade_data = month_data.iloc[i]

        try:
            last_trade_date = datetime.datetime.strptime(trade_data.trade_date, '%Y%m%d')
            first_trade_date = datetime.date(last_trade_date.year, last_trade_date.month, 1)
        except Exception as e:
            continue

        exist_smt = SMT.objects(Q(stock_number=stock_number) & Q(last_trade_date=last_trade_date))
        if exist_smt and len(exist_smt) > 0:
            smt = exist_smt[0]
        else:
            smt = SMT(stock_number=stock_number)
            smt.first_trade_date = first_trade_date
            smt.last_trade_date = last_trade_date

        smt.month_open_price = trade_data.open
        smt.month_highest_price = trade_data.high
        smt.month_lowest_price = trade_data.low
        smt.month_close_price = trade_data.close
        smt.turnover_volume = trade_data.vol
        smt.turnover_amount = trade_data.amount
        try:
            smt.save()
        except Exception as e:
            logging.error("save SMT error: %s" % str(e))
            continue


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'用tushare pro api采集月线行情数据')
    parser.add_argument(u'-s', action=u'store', dest='start_date', required=False, help=u'开始采集日期')
    parser.add_argument(u'-e', action=u'store', dest='end_date', required=False, help=u'结束采集日期')

    args = parser.parse_args()
    if args.start_date and args.end_date:
        try:
            start_date = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(args.end_date, '%Y-%m-%d')
        except Exception as e:
            print('Wrong date form')
            raise e
    else:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=365)

    return start_date, end_date


if __name__ == '__main__':
    start_date, end_date = setup_argparse()
    setup_logging(__file__, logging.WARNING)
    logging.info('Start collect history trading data')
    begin_collect_month_trading(start_date, end_date)
    logging.info('Collect history trading data success')