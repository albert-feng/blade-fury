#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import datetime
import time
import random
import argparse

from mongoengine import Q

from collector import tushare_util
from logger import setup_logging
from models import StockInfo, StockDailyTrading as SDT


timeout = 30
query_step = 100


def collect_his_trading(stock_number, stock_name, start_date, end_date):
    ts_code = tushare_util.gen_ts_code(stock_number)

    his_data = tushare_util.get_pro_client().query('daily', ts_code=ts_code, start_date=start_date.strftime('%Y%m%d'),
                                                   end_date=end_date.strftime('%Y%m%d'))
    for i in range(0, len(his_data)):
        trade_data = his_data.iloc[i]
        try:
            date = datetime.datetime.strptime(trade_data.trade_date, '%Y%m%d')
        except Exception as e:
            continue

        existSdt = SDT.objects(Q(stock_number=stock_number) & Q(date=date))
        if existSdt and len(existSdt) > 0:
            sdt = existSdt[0]
        else:
            sdt = SDT(stock_number=stock_number)
            sdt.date = date

        sdt.stock_name = stock_name
        sdt.yesterday_closed_price = trade_data.pre_close
        sdt.today_opening_price = trade_data.open
        sdt.today_closing_price = trade_data.close
        sdt.today_highest_price = trade_data.high
        sdt.today_lowest_price = trade_data.low
        sdt.turnover_amount = trade_data.amount
        sdt.turnover_volume = trade_data.vol
        sdt.increase_amount = trade_data.change
        sdt.increase_rate = str(trade_data.pct_chg) + '%'
        try:
            sdt.save()
        except Exception as e:
            continue


def begin_collect_his(start_date, end_date):
    stock_info = StockInfo.objects()
    stock_count = stock_info.count()
    skip = 0

    while skip < stock_count:
        try:
            stocks = StockInfo.objects().skip(skip).limit(query_step)
        except Exception as e:
            logging.error('Error when query skip %s  StockInfo:%s' % (skip, e))
            stocks = []

        for i in stocks:
            try:
                collect_his_trading(i.stock_number, i.stock_name, start_date, end_date)
            except Exception as e:
                logging.error('Collect %s his data failed:%s' % (i.stock_number, e))
            finally:
                time.sleep(random.random())
        skip += query_step


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'用tushare pro api采集日线行情数据')
    parser.add_argument(u'-s', action=u'store', dest='start_date', required=True, help=u'开始采集日期')
    parser.add_argument(u'-e', action=u'store', dest='end_date', required=True, help=u'结束采集日期')

    args = parser.parse_args()
    try:
        start_date = datetime.datetime.strptime(args.start_date, '%Y%m%d')
        end_date = datetime.datetime.strptime(args.end_date, '%Y%m%d')
    except Exception as e:
        print('Wrong date form')
        raise e

    return start_date, end_date


if __name__ == '__main__':
    start_date, end_date = setup_argparse()
    setup_logging(__file__, logging.WARNING)
    logging.info('Start collect history trading data')
    begin_collect_his(start_date, end_date)
    logging.info('Collect history trading data success')
