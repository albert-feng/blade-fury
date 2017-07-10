#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
import platform
import datetime

from mongoengine import Q

from models import StockNotice as SN

day_delta = 20
trading_market = {'60': u'沪市主板', '000': u'深市主板', '002': u'中小板', '300': u'创业板'}


def query_stock_notice(date, keyword=u'购买理财产品'):
    sn = SN.objects(Q(notice_title__contains=keyword) & Q(notice_date__gte=date))

    stocks = list(set([(i.stock_number, i.stock_name) for i in sn]))
    stocks.sort()
    print(len(stocks))
    for k, v in trading_market.iteritems():
        filtered_stocks = [s for s in stocks if s[0].startswith(k)]
        print('---------%s---%s---------' % (v, len(filtered_stocks)))
        for i in filtered_stocks:
            print(i[0], i[1])


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'查询近期公告包含某个关键字的股票')
    parser.add_argument(u'-k', action=u'store', dest='keyword', required=True, help=u'需要查询的板块')

    args = parser.parse_args()
    return args.keyword


if __name__ == '__main__':
    keyword = setup_argparse()
    if isinstance(keyword, str):
        if platform.system() == 'Windows':
            keyword = keyword.decode('gb2312')
        else:
            keyword = keyword.decode('utf-8')

    t = datetime.date.today() - datetime.timedelta(days=20)
    query_stock_notice(t, keyword=keyword)
