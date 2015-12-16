#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
根据均线系统来进行选股
"""


import argparse
import logging

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
        ma_list.insert(0, calculate_ma(sdt_list[i: ma+i]))
    return ma_list


def calculate_ma_difference(li_1, li_2):
    ma_difference = []
    if len(li_1) == len(li_2):
        for i in xrange(0, len(li_1)):
            ma_difference.append(round(li_1[i]-li_2[i], 2))

        return ma_difference


def is_growing(data):
    for i in xrange(0, len(data)-1):
        if data[i] > data[i+1]:
            return False
    return True


def check_duplicate(stock_number, date, strategy_name):
    cursor = QR.objects(Q(stock_number=stock_number) & Q(date=date) & Q(strategy_name=strategy_name))

    if cursor:
        return True
    else:
        return False


def save_quant_result(sdt, strategy_name):
    if isinstance(sdt, SDT):
        stock_number = sdt.stock_number
        stock_name = sdt.stock_name
        date = sdt.date
        strategy_name = strategy_name
        init_price = sdt.today_closing_price

        if not check_duplicate(stock_number, date, strategy_name):
            qr = QR(stock_number=stock_number, stock_name=stock_name, date=date, strategy_name=strategy_name,
                    init_price=init_price)
            qr.save()


def quant_stock(stock_number, short_ma=1, long_ma=30):
    strategy_name = 'ma_long_%s_%s' % (short_ma, long_ma)
    sdt = SDT.objects(stock_number=stock_number).order_by('-date')[:long_ma+10]

    if sdt.count() < long_ma + 5:
        """
        如果交易数据不够，跳过
        """
        return
    if float(sdt[0].increase_rate.replace('%', '')) == 0.0 and float(sdt[0].turnover_rate.replace('%', '')) == 0.0:
        """
        如果最新一天股票的状态是停牌，跳过
        """
        return
    if sdt[0].today_closing_price <= 10.0:
        """
        去掉当日收盘价低于10块的票
        """
        return

    # 计算出连续3个交易日长MA和短MA的值
    trading_data = []
    for i in sdt:
        """
        去除交易数据里的停牌数据
        """
        if float(i.increase_rate.replace('%', '')) == 0.0 and float(i.turnover_rate.replace('%', '')) == 0.0:
            continue
        else:
            trading_data.append(i)

    short_ma_list = calculate_ma_list(trading_data, short_ma, 3)
    long_ma_list = calculate_ma_list(trading_data, long_ma, 3)
    ma_difference = calculate_ma_difference(short_ma_list, long_ma_list)

    if ma_difference[-2] < 0 < ma_difference[-1]:
        """
        当短期均线向上穿过长期均线的时候
        """
        save_quant_result(trading_data[0], strategy_name)

    if ma_difference[-1] <= 0 and abs(ma_difference[-1])/trading_data[0].today_closing_price <= 0.05\
            and is_growing(ma_difference):
        """
        当两根均线持续三天靠近，且数量差距小于等于5%的时候
        """
        save_quant_result(trading_data[0], strategy_name)


def start_quant_analysis(short_ma=1, long_ma=30):
    try:
        all_stocks = StockInfo.objects()
    except Exception, e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    stocks_count = len(all_stocks)
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
                quant_stock(i.stock_number, short_ma, long_ma)
            except Exception, e:
                logging.error('Error when collect %s notice: %s' % (i.stock_number, e))
        skip += query_step


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据长短均线的金叉来选股')
    parser.add_argument(u'-s', action=u'store', dest='short_ma', required=True, help=u'短期均线数')
    parser.add_argument(u'-l', action=u'store', dest='long_ma', required=True, help=u'长期均线数')

    args = parser.parse_args()
    return int(args.short_ma), int(args.long_ma)


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    short_ma, long_ma = setup_argparse()
    start_quant_analysis(short_ma, long_ma)
