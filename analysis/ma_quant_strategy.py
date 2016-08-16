#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
根据均线系统来进行选股
"""


import argparse
import logging
import datetime

from mongoengine import Q

from logger import setup_logging
from models import StockInfo, StockDailyTrading as SDT, QuantResult as QR


query_step = 100  # 一次从数据库中取出的数据量


def calculate_ma(sdt_list):
    number = 0
    for i in sdt_list:
        if isinstance(i, SDT):
            number += i.today_closing_price

    return round(number/len(sdt_list), 2)


def calculate_ma_list(sdt_list, ma, ma_amount=3):
    ma_list = []
    for i in xrange(0, ma_amount):
        ma_list.append(calculate_ma(sdt_list[i: ma+i]))
    return ma_list


def calculate_ma_difference(li_1, li_2):
    ma_difference = []
    if len(li_1) == len(li_2):
        for i in xrange(0, len(li_1)):
            ma_difference.append(round(li_1[i]-li_2[i], 2))

        return ma_difference


def check_duplicate(stock_number, date, strategy_name):
    cursor = QR.objects(Q(stock_number=stock_number) & Q(date=date) & Q(strategy_name=strategy_name))

    if cursor:
        return True
    else:
        return False


def save_quant_result(sdt, strategy_name, strategy_direction='long'):
    if isinstance(sdt, SDT):
        stock_number = sdt.stock_number
        stock_name = sdt.stock_name
        date = sdt.date
        strategy_name = strategy_name
        init_price = sdt.today_closing_price

        if not check_duplicate(stock_number, date, strategy_name):
            qr = QR(stock_number=stock_number, stock_name=stock_name, date=date, strategy_name=strategy_name,
                    init_price=init_price, strategy_direction=strategy_direction)
            qr.save()


def quant_stock(stock_number, short_ma_num, long_ma_num, qr_date):
    sdt = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) & Q(date__lte=qr_date)).order_by('-date')

    if not sdt:
        # return if not trading data
        return
    if short_ma_num <= long_ma_num:
        strategy_direction = 'long'
    else:
        strategy_direction = 'short'

    strategy_name = 'ma_%s_%s_%s' % (strategy_direction, short_ma_num, long_ma_num)

    short_ma_list = calculate_ma_list(sdt[:short_ma_num+5], short_ma_num, 2)
    long_ma_list = calculate_ma_list(sdt[:long_ma_num+5], long_ma_num, 2)
    ma_difference = calculate_ma_difference(short_ma_list, long_ma_list)

    if ma_difference[0] > 0 > ma_difference[1]:
        """
        当短期均线向上穿过长期均线的时候
        """
        save_quant_result(sdt[0], strategy_name, strategy_direction)


def start_quant_analysis(short_ma_num, long_ma_num, qr_date):
    if not SDT.objects(date=qr_date).count():
        print 'Not a Trading Date'
        return

    try:
        all_stocks = StockInfo.objects()
    except Exception, e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    stocks_count = all_stocks.count()
    skip = 0

    while skip < stocks_count:
        try:
            stocks = StockInfo.objects().skip(skip).limit(query_step)
        except Exception, e:
            logging.error('Error when query skip %s  StockInfo:%s' % (skip, e))
            stocks = []

        for i in stocks:
            if i.account_firm and u'瑞华会计师' in i.account_firm:
                # 过滤瑞华的客户
                continue

            try:
                quant_stock(i.stock_number, short_ma_num, long_ma_num, qr_date)
            except Exception, e:
                logging.error('Error when quant %s ma strategy: %s' % (i.stock_number, e))
        skip += query_step


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据长短均线的金叉来选股')
    parser.add_argument(u'-s', action=u'store', dest='short_ma', required=True, help=u'短期均线数')
    parser.add_argument(u'-l', action=u'store', dest='long_ma', required=True, help=u'长期均线数')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算均线的日期')

    args = parser.parse_args()

    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y-%m-%d')
        except Exception, e:
            print 'Wrong date form'
            raise e
    else:
        qr_date = datetime.date.today()

    return int(args.short_ma), int(args.long_ma), qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    short_ma, long_ma, qr_date = setup_argparse()
    start_quant_analysis(short_ma, long_ma, qr_date)
