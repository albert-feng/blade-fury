#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用来获取一个股票每天的交易数据
"""


import datetime
import logging
import argparse

from mongoengine import Q

from models import StockDailyTrading as SDT
from logger import setup_logging
from collector.tushare_util import get_pro_client


def collect_stock_daily_trading(date):
    trading_data = get_pro_client().daily(trade_date=date.strftime('%Y%m%d'))

    for i in range(0, len(trading_data)):
        stock = trading_data.iloc[i]
        stock_number = stock.ts_code.split('.')[0]

        existSdt = SDT.objects(Q(stock_number=stock_number) & Q(date=date))
        if existSdt and len(existSdt) > 0:
            sdt = existSdt[0]
        else:
            sdt = SDT(stock_number=stock_number)

        sdt.yesterday_closed_price = stock.pre_close
        sdt.today_opening_price = stock.open
        sdt.today_closing_price = stock.close
        sdt.today_highest_price = stock.high
        sdt.today_lowest_price = stock.low
        sdt.turnover_amount = stock.amount
        sdt.turnover_volume = stock.vol
        sdt.increase_amount = stock.change
        sdt.increase_rate = str(stock.pct_chg) + '%'
        sdt.save()


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'用tushare pro api采集日线行情数据')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算均线的日期')

    args = parser.parse_args()
    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y%m%d')
        except Exception as e:
            print('Wrong date form')
            raise e
    else:
        today = datetime.date.today()
        qr_date = datetime.datetime(year=today.year, month=today.month, day=today.day)

    return qr_date


def main():
    setup_logging(__file__, logging.WARNING)
    date = setup_argparse()
    logging.info('Start Collect %s Trading Data' % datetime.date.today())
    collect_stock_daily_trading(date)
    logging.info('Collect %s Trading Data Success' % datetime.date.today())


if __name__ == '__main__':
    main()
