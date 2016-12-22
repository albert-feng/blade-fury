#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
import logging
import json
import codecs
from os.path import exists

from mongoengine import Q
import pandas as pd
from pandas import DataFrame

from logger import setup_logging
from models import StockInfo,StockNotice as SN
from models import StockDailyTrading as SDT


mining_keywords = [u'要约收购', u'协议收购', u'异常波动', u'权益变动', u'股东增持', u'股票异动', u'交易异常',
                   u'受让', u'股份转让', u'购买资产', u'资产出售', u'资产重组']
time_interval = 0
timeout = 30  # 发送http请求的超时时间
query_step = 30  # 一次从数据库中取出的数据量


def collect_event_notice(stock_number):
    global time_interval
    today = datetime.date.today()
    delta = datetime.timedelta(days=time_interval)

    cursor = SN.objects(Q(stock_number=stock_number) & Q(date__gte=today-delta)).order_by('date')
    if not cursor:
        return []

    notice = []
    for n in cursor:
        for i in mining_keywords:
            if i in n.title:
                notice.append({'title': n.title, 'date': n.date, 'stock_number': n.stock_number})
                break
    return notice


def start_mining_notice():
    try:
        all_stocks = StockInfo.objects()
    except Exception, e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    stocks_count = len(all_stocks)
    skip = 0

    notice_data = []
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

            sdt = SDT.objects(Q(stock_number=i.stock_number) & Q(date=datetime.date.today()))
            if not sdt:
                # 过滤仍在停牌的票
                continue

            try:
                notice = collect_event_notice(i.stock_number)
            except Exception, e:
                logging.error('Error when collect %s notice: %s' % (i.stock_number, e))
            if notice:
                notice_data += notice
        skip += query_step

    if not notice_data:
        return
    df = DataFrame(notice_data).sort_values(by=['stock_number', 'date'], ascending=[True, True])\
                               .set_index(['stock_number', 'date'])
    pd.set_option('display.width', 400)
    pd.set_option('display.max_colwidth', 150)
    pd.set_option('display.max_rows', 800)

    notice_path = '/root/healing-ward/notice_mining/%s.txt' % datetime.date.today()
    notice_data =  df.to_string()
    if exists(notice_path):
        print notice_data
    else:
        with codecs.open(notice_path, 'w+', 'utf-8') as fd:
            fd.write(notice_data)

    pd.set_option('display.width', None)
    pd.set_option('display.max_rows', None)


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock detail info')
    start_mining_notice()
    logging.info('Collect stock detail info Success')

