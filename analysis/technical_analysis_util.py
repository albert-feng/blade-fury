#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime
import json

import requests
import numpy as np
import talib as ta
import pandas as pd
from pandas import DataFrame
from models import QuantResult as QR, StockDailyTrading as SDT, StockInfo
from mongoengine import Q
from config import eastmoney_stock_api


query_step = 100
timeout = 60
retry = 5


def format_trading_data(sdt):
    trading_data = []
    standard_total_stock = sdt[1].total_stock if sdt[1].total_stock else sdt[2].total_stock
    if not standard_total_stock:
        return trading_data

    for i in sdt:
        if not i.total_stock:
            close_price = i.today_closing_price
            high_price = i.today_highest_price
            low_price = i.today_lowest_price
        else:
            if standard_total_stock == i.total_stock:
                close_price = i.today_closing_price
                high_price = i.today_highest_price
                low_price = i.today_lowest_price
            else:
                close_price = i.today_closing_price * i.total_stock / standard_total_stock
                high_price = i.today_highest_price * i.total_stock / standard_total_stock
                low_price = i.today_lowest_price * i.total_stock / standard_total_stock
        trading_data.append({'date': i.date, 'close_price': close_price, 'high_price': high_price,
                             'low_price': low_price, 'quantity_relative_ratio': i.quantity_relative_ratio,
                             'turnover_amount': i.turnover_amount})
    trading_data = sorted(trading_data, key=lambda x: x['date'], reverse=False)
    return trading_data


def calculate_macd(df, short_ema, long_ema, dif_ema):
    if isinstance(df, DataFrame):
        if df.index.name != 'date':
            df = df.set_index(['date'])
        df['short_ema'] = df['close_price'].ewm(span=short_ema).mean()
        df['long_ema'] = df['close_price'].ewm(span=long_ema).mean()
        df['dif'] = df['short_ema'] - df['long_ema']
        df['dea'] = df['dif'].ewm(span=dif_ema).mean()
        df['macd'] = df['dif'] - df['dea']
        return df
    else:
        raise Exception('df type is wrong')


def calculate_ma(df, short_ma, long_ma):
    if isinstance(df, DataFrame):
        if df.index.name != 'date':
            df = df.set_index(['date'])
        df['short_ma'] = df['close_price'].rolling(window=short_ma, center=False).mean()
        df['long_ma'] = df['close_price'].rolling(window=long_ma, center=False).mean()
        df['diff_ma'] = df['short_ma'] - df['long_ma']
        return df
    else:
        raise Exception('df type is wrong')


def calculate_kdj(df, fastk_period=9):
    if isinstance(df, DataFrame):
        if df.index.name != 'date':
            df = df.set_index(['date'])
        df['k'], df['d'] = ta.STOCH(np.array(df['high_price']), np.array(df['low_price']), np.array(df['close_price']),
                                    fastk_period=fastk_period, slowk_period=3, slowk_matype=0, slowd_period=3,
                                    slowd_matype=0)
        df['k_d_dif'] = df['k'] - df['d']
        return df
    else:
        raise Exception('df type is wrong')


def check_duplicate_strategy(qr):
    if isinstance(qr, QR):
        try:
            cursor = QR.objects(Q(stock_number=qr.stock_number) & Q(strategy_name=qr.strategy_name) &
                                Q(date=qr.date))
        except Exception, e:
            logging.error('Error when check dupliate %s strategy %s date %s: %s' % (qr.stock_number, qr.strategy_name,
                                                                                    qr.date, e))
        if cursor:
            return True
        else:
            return False


def start_quant_analysis(**kwargs):
    if not kwargs.get('qr_date'):
        print 'no qr_date'
        return
    if not kwargs.get('quant_stock'):
        print 'not quant_stock funtion'
        return

    if not SDT.objects(date=kwargs['qr_date']) and not kwargs.get('real_time'):
        print 'Not a Trading Date'
        return

    try:
        all_stocks = StockInfo.objects()
    except Exception, e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    stocks_count = all_stocks.count()
    skip = 0
    quant_res = []

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

            qr = ''
            try:
                qr = kwargs['quant_stock'](i.stock_number, i.stock_name, **kwargs)
            except Exception, e:
                logging.error('Error when quant %s ma strategy: %s' % (i.stock_number, e))
            if isinstance(qr, QR):
                quant_res.append(qr)
        skip += query_step
    return quant_res


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
        quantity_relative_ratio = stock[22]
        sdt.quantity_relative_ratio = 0 if quantity_relative_ratio == '-' else float(quantity_relative_ratio)
        sdt.turnover_rate = stock[23]
        sdt.date = datetime.datetime.combine(datetime.date.today(), datetime.time(0,0))

        if sdt.turnover_amount == 0:
            # 去掉停牌的交易数据
            continue
        today_trading[stock_number] = sdt
    return today_trading


def display_quant(real_time_res):
    quant_data = [{'stock_number': i.stock_number, 'stock_name': i.stock_name, 'price': i.init_price}
                  for i in real_time_res]
    df = DataFrame(quant_data).set_index('stock_number').sort_index().reindex(columns=['stock_name', 'price'])
    pd.set_option('display.max_rows', len(real_time_res) + 10)
    print df
    pd.reset_option('display.max_rows')
