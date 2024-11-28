#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime
import json

import tushare as ts
import requests
import pandas as pd
from pandas import DataFrame
from models import QuantResult as QR, StockDailyTrading as SDT, StockInfo, StockWeeklyTrading as SWT
from mongoengine import Q
from config import eastmoney_stock_api, banned_stock, tushare_token
from collector.collect_util import estimate_market, get_tushare_month_trading

query_step = 100
timeout = 60
retry = 5
year_num = 250


pro = ts.pro_api(tushare_token)

def format_trading_data(stock_trading_data, use_ad_price=False):
    trading_data = []

    if isinstance(stock_trading_data[0], SDT):
        for i in stock_trading_data:
            close_price = i.today_closing_price
            high_price = i.today_highest_price
            low_price = i.today_lowest_price
            trading_data.append({'date': i.date, 'close_price': close_price, 'high_price': high_price,
                                 'low_price': low_price})

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


def pre_sdt_check(stock_number, **kwargs):
    """
    依据量价进行预先筛选
    :param stock_number:
    :param qr_date:
    :return:
    """
    if stock_number.startswith('8'):
        # 过滤北交所的票
        return

    qr_date = kwargs.get('qr_date')
    rate_value = 0
    cursor = SDT.objects(Q(stock_number=stock_number) & Q(today_closing_price__ne=0.0) & Q(date__lte=qr_date))\
        .order_by('-date')
    if not cursor:
        return False

    min_total_value = 2000000000
    stock_info = StockInfo.objects(stock_number=stock_number)

    if stock_info and stock_info[0].total_value and stock_info[0].total_value < min_total_value:
        return False

    return True


def is_week_long(stock_number, qr_date, short_ma, long_ma):
    if short_ma < long_ma:
        quant_count = long_ma + 5
    else:
        quant_count = short_ma + 5

    swt = SWT.objects(Q(stock_number=stock_number) &
                      Q(last_trade_date__lte=qr_date)).order_by('-last_trade_date')[:quant_count]
    if not swt:
        return False

    use_ad_price = True
    trading_data = format_trading_data(swt, use_ad_price)
    df = calculate_ma(DataFrame(trading_data), short_ma, long_ma)
    this_week = df.iloc[-1]
    if this_week['diff_ma'] > 0:
        return True
    else:
        return False


def cal_year_ma(cursor):
    sdt = cursor[:year_num + 5]
    trading_data = format_trading_data(sdt)
    if not trading_data:
        return False
    df = DataFrame(trading_data)
    df['year_ma'] = df['close_price'].rolling(window=year_num, center=False).mean()
    today_ma = df.iloc[-1]
    return round(today_ma['year_ma'], 4)


def cal_turnover_ma(cursor, count):
    amount_sdt = cursor[:count]
    amount_li = [i.turnover_amount for i in amount_sdt]
    amount_avg = sum(amount_li) / len(amount_li)
    return amount_avg


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
    """

    :param kwargs:{
        qr_date: 运行策略时间
    }
    :return:
    """

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

            if i.stock_number in banned_stock:
                continue

            if not kwargs.get('real_time') and\
               not SDT.objects(Q(date=kwargs['qr_date']) & Q(stock_number=i.stock_number)):
                continue

            qr = ''
            kwargs['industry_involved'] = i.industry_involved
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
        if stock[4] == '-':
            continue
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


def setup_realtime_swt(swt, stock_number, qr_date):
    # 当没有当周数据时，用日线数据补
    sdt = SDT.objects(Q(stock_number=stock_number) & Q(date=qr_date))
    if not sdt:
        return list()

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
            return list()

        sdt = list(sdt)
        sdt.insert(0, today_trading.get(stock_number))
    return sdt


def is_ad_price(stock_number, qr_date, swt):
    use_ad_price = True
    if swt[0].last_trade_date < qr_date:
        use_ad_price = False
        swt = setup_realtime_swt(swt, stock_number, qr_date)
    if not swt[0].ad_close_price:
        use_ad_price = False
    return use_ad_price, swt


def get_month_trading(stock_number, start_date=None, end_date=None):
    return get_tushare_month_trading(stock_number, start_date, end_date)


def get_week_trading(stock_number, start_date=None, end_date=None):
    return get_trading_from_tushare(stock_number, start_date=start_date, end_date=end_date, ktype='W')


def get_trading_from_tushare(stock_number, start_date=None, end_date=None, ktype='D', autype='qfq'):
    month_trading_data = ts.get_k_data(stock_number, ktype=ktype, autype=autype, start=start_date, end=end_date)
    df = month_trading_data.set_index(['date'])
    df['close_price'] = df['close']
    return df


def calculate_highest_rate(sdt: SDT) -> float:
    """
    计算给定股票数据对象的最高比率。

    该函数通过比较股票的当日最高价和前日收盘价来计算最高比率。
    最高比率是衡量股票价格日内波动的一个重要指标。

    参数:
    sdt (SDT): 一个包含股票数据的SDT对象。SDT对象应至少包含以下属性：
        - today_highest_price: 当日最高价
        - yesterday_closed_price: 前日收盘价

    返回:
    float: 最高比率，以百分比形式返回。

    示例:
    >>> sdt = SDT(today_highest_price=120, yesterday_closed_price=100)
    >>> calculate_highest_rate(sdt)
    20.0
    """
    # 计算最高比率的公式：(当日最高价 - 前日收盘价) / 前日收盘价 * 100
    return (sdt.today_highest_price - sdt.yesterday_closed_price) / sdt.yesterday_closed_price * 100
