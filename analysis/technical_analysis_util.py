#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime
import json

import requests
import pandas as pd
from pandas import DataFrame
from models import QuantResult as QR, StockDailyTrading as SDT, StockInfo, StockWeeklyTrading as SWT
from mongoengine import Q
from config import eastmoney_stock_api


query_step = 100
timeout = 60
retry = 5
year_num = 250


def format_trading_data(stock_trading_data, use_ad_price=False):
    trading_data = []

    if isinstance(stock_trading_data[0], SDT):
        standard_total_stock = stock_trading_data[1].total_stock if stock_trading_data[1].total_stock\
                               else stock_trading_data[2].total_stock
        if not standard_total_stock:
            return trading_data

        for i in stock_trading_data:
            if not i.total_stock:
                close_price = i.today_closing_price
                high_price = i.today_highest_price
                low_price = i.today_lowest_price
            else:
                if standard_total_stock/i.total_stock < 2:
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

    elif isinstance(stock_trading_data[0], SWT):
        for i in stock_trading_data:
            if use_ad_price:
                close_price = i.ad_close_price
            else:
                close_price = i.weekly_close_price
            trading_data.append({
                'date': i.last_trade_date,
                'close_price': close_price,
            })

    if trading_data:
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


def check_year_ma(stock_number, qr_date):
    """
    去掉年线以下的
    :param stock_number:
    :param qr_date:
    :return:
    """
    cursor = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) & Q(date__lte=qr_date))
    if not cursor:
        return False

    sdt = cursor.order_by('-date')[:year_num+5]
    trading_data = format_trading_data(sdt)
    if not trading_data:
        return False
    df = DataFrame(trading_data)
    df['year_ma'] = df['close_price'].rolling(window=year_num, center=False).mean()
    today_ma = df.iloc[-1]
    if today_ma['close_price'] > today_ma['year_ma']:
        return True
    else:
        return False


def check_duplicate_strategy(qr):
    if isinstance(qr, QR):
        try:
            cursor = QR.objects(Q(stock_number=qr.stock_number) & Q(strategy_name=qr.strategy_name) &
                                Q(date=qr.date))
        except Exception as e:
            logging.error('Error when check dupliate %s strategy %s date %s: %s' % (qr.stock_number, qr.strategy_name,
                                                                                    qr.date, e))
        if cursor:
            return True
        else:
            return False


def start_quant_analysis(**kwargs):
    if not kwargs.get('qr_date'):
        print('no qr_date')
        return
    if not kwargs.get('quant_stock'):
        print('not quant_stock funtion')
        return

    if not SDT.objects(date=kwargs['qr_date']) and not kwargs.get('real_time'):
        print('Not a Trading Date')
        return

    try:
        all_stocks = StockInfo.objects()
    except Exception as e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    stocks_count = all_stocks.count()
    skip = 0
    quant_res = []

    while skip < stocks_count:
        try:
            stocks = StockInfo.objects().skip(skip).limit(query_step)
        except Exception as e:
            logging.error('Error when query skip %s  StockInfo:%s' % (skip, e))
            stocks = []

        for i in stocks:
            if i.account_firm and u'瑞华会计师' in i.account_firm:
                # 过滤瑞华的客户
                continue

            if not SDT.objects(Q(date=kwargs['qr_date']) & Q(stock_number=i.stock_number)):
                continue

            qr = ''
            try:
                qr = kwargs['quant_stock'](i.stock_number, i.stock_name, **kwargs)
            except Exception as e:
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
        # 'Host': 'hqdigi2.eastmoney.com',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36'
    }

    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        r.encoding = 'utf-8'
    except Exception as e:
        logging.error('Request url %s failed: %s' % (url, e))
        raise e

    try:
        data = json.loads(r.text.replace('var js=', '').replace('rank', '\"rank\"').replace('pages', '\"pages\"'))
    except Exception as e:
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
    print(df)
    pd.reset_option('display.max_rows')


def setup_realtime_swt(swt, stock_number):
    # 当没有当周数据时，用日线数据补
    sdt = SDT.objects(Q(stock_number=stock_number) & Q(date=qr_date))
    if not sdt:
        return

    qr_date_trading = sdt[0]
    extra_swt = SWT()
    extra_swt.weekly_close_price = qr_date_trading.today_closing_price
    extra_swt.last_trade_date = qr_date_trading.date
    swt = list(swt)
    swt.insert(0, extra_swt)
    return swt

def setup_realtime_sdt(stock_number, sdt, kwargs):
    today_sdt = SDT.objects(date=kwargs['qr_date'])
    if kwargs['qr_date'] == datetime.date.today() and not today_sdt:
        today_trading = kwargs.get('today_trading', {})
        if not today_trading.get(stock_number):
            return

        sdt = list(sdt)
        sdt.insert(0, today_trading.get(stock_number))
    return sdt
