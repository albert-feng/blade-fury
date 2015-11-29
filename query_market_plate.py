#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'fengweigang'


from models import StockInfo


def query_market_plate_stock(plate):
    """
    查询某个板块的个股
    """
    stock_info = StockInfo.objects().timeout(False)
    stocks = []
    filtered_firm = u'瑞华会计师事务所'

    for i in stock_info:
        for j in i.market_plate:
            if plate in j and filtered_firm not in i.account_firm:
                stocks.append(i)
                break
    return stocks


if __name__ == '__main__':
    plate = u'酿酒'
    stocks = query_market_plate_stock(plate)

    for i in stocks:
        print i.stock_number, i.stock_name

    print len(stocks)
