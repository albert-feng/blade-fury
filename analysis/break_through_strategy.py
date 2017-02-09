#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import argparse
import json

import requests
from mongoengine import Q
import pandas as pd
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import format_trading_data, check_duplicate_strategy
from analysis.technical_analysis_util import calculate_ma, start_quant_analysis
from config import eastmoney_stock_api


ema_volume = 150
timeout = 60
retry = 5


def request_and_handle_data(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Host': 'hqdigi2.eastmoney.com',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36'
    }

    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.encoding = 'utf-8'
    except Exception, e:
        logging.error('Request url %s failed: %s' % (url, e))
        raise e

    try:
        data = json.loads(r.text.replace('var js=', '').replace('rank', '\"rank\"').replace('pages', '\"pages\"'))
    except Exception, e:
        logging.error('Handle data failed:' + str(e))
        raise e

    return data


def collect_stock_daily_trading():
    """
    获取并保存每日股票交易数据
    """
    url = eastmoney_stock_api
    data = {}
    global retry
    while retry > 0:
        try:
            data = request_and_handle_data(url)
            retry = 0
        except Exception:
            retry -= 1

    stock_data = data.get('rank', [])
    today_trading = {}
    for i in stock_data:
        stock = i.split(',')
        stock_number = stock[1]
        stock_name = stock[2]
        sdt = SDT(stock_number=stock_number, stock_name=stock_name)
        sdt.yesterday_closed_price = float(stock[3])
        sdt.today_opening_price = float(stock[4])
        sdt.today_closing_price = float(stock[5])
        sdt.today_highest_price = float(stock[6])
        sdt.today_lowest_price = float(stock[7])
        sdt.turnover_amount = int(stock[8])
        sdt.turnover_volume = int(stock[9])
        sdt.increase_amount = float(stock[10])
        sdt.increase_rate = stock[11]
        sdt.today_average_price = float(stock[12])
        sdt.quantity_relative_ratio = float(stock[22])
        sdt.turnover_rate = stock[23]

        if float(sdt.turnover_rate.replace('%', '')) == 0.0:
            # 去掉停牌的交易数据
            continue
        today_trading[stock_number] = sdt
    return today_trading


def quant_stock(stock_number, stock_name, **kwargs):
    real_time = kwargs.get('real_time', False)
    strategy_direction = 'long'
    strategy_name = 'break_through_%s_%s_%s' % (strategy_direction, kwargs['short_ma'], kwargs['long_ma'])

    sdt = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) &
                      Q(date__lte=kwargs['qr_date'])).order_by('-date')[:ema_volume]

    if len(sdt) < ema_volume-50:
        return
    if float(sdt[0].increase_rate.replace('%', '')) > 9:
        return
    if sdt[0].today_closing_price <= sdt[0].today_average_price:
        return
    if sdt[0].turnover_amount <= sdt[1].turnover_amount:
        return

    today_sdt = SDT.objects(date=kwargs['qr_date'])
    if kwargs['qr_date'] == datetime.date.today() and not today_sdt:
        today_trading = collect_stock_daily_trading
        if not today_trading.get(stock_number):
            return

        sdt = list(sdt)
        sdt.insert(0, today_trading.get(stock_number))

    trading_data = format_trading_data(sdt)
    df = calculate_ma(DataFrame(trading_data), short_ma, long_ma)
    today = df.iloc[-1]
    yestoday = df.iloc[-2]

    break_through = 1.8
    if yestoday['close_price'] < yestoday['short_ma'] and yestoday['close_price'] < yestoday['long_ma']\
        and today['close_price'] > today['short_ma'] and today['close_price'] > today['long_ma']\
        and today['quantity_relative_ratio'] > break_through:
        qr = QR(
            stock_number=stock_number, stock_name=stock_name, date=today.name,
            strategy_direction=strategy_direction, strategy_name=strategy_name,
            init_price=today['close_price']
        )

        if real_time:
            return qr
        if not check_duplicate_strategy(qr):
            qr.save()
            return qr
    return ''


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'根据突破短均线的策略选股')
    parser.add_argument(u'-s', action=u'store', dest='short_ma', required=True, help=u'短期均线数')
    parser.add_argument(u'-l', action=u'store', dest='long_ma', required=True, help=u'长期均线数')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'计算均线的日期')
    parser.add_argument(u'-r', action=u'store_true', dest='real_time', required=False, help=u'是否实时计算')

    args = parser.parse_args()

    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y-%m-%d')
        except Exception, e:
            print 'Wrong date form'
            raise e
    else:
        qr_date = datetime.date.today()

    return int(args.short_ma), int(args.long_ma), qr_date, args.real_time


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    short_ma, long_ma, qr_date, real_time = setup_argparse()
    real_time_res = start_quant_analysis(short_ma=short_ma, long_ma=long_ma, qr_date=qr_date, quant_stock=quant_stock,
                                         real_time=real_time)
    if real_time_res and real_time:
        quant_data = [{'stock_number': i.stock_number, 'stock_name': i.stock_name, 'price': i.init_price}
                      for i in real_time_res]
        df = DataFrame(quant_data).set_index('stock_number')
        pd.set_option('display.max_rows', len(real_time_res) + 10)
        print df
        pd.reset_option('display.max_rows')
