#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import platform

from models import StockInfo
from models import StockDailyTrading as SDT


def query_market_plate_stock(market_plate, filter_ruihua=True):
    """
    查询某个板块的个股
    """
    stock_info = StockInfo.objects().timeout(False)
    stocks = []
    filtered_firm = u'瑞华会计师事务所'

    for i in stock_info:
        for j in i.market_plate:
            if market_plate in j:
                if filter_ruihua and filtered_firm not in i.account_firm:
                    # 由于老爸是瑞华会计师事务所的，我不能买卖这家事务所出具报告的上市公司股票
                    stocks.append(i)
                    break
                elif not filter_ruihua:
                    stocks.append(i)
                    break
    return stocks


def query_latest_trading(stock_number):
    sdt = SDT.objects(stock_number=stock_number).order_by('-date')[0]
    return sdt


def main(market_plate=u'创业板', filter_ruihua=True):
    stocks = query_market_plate_stock(market_plate, filter_ruihua)

    plate_stocks = []
    for i in stocks:
        sdt = query_latest_trading(i.stock_number)
        if sdt.today_closing_price > 0:
            item = {'stock_number': i.stock_number, 'stock_name': i.stock_name, 'increase_rate': sdt.increase_rate,
                    'today_closing_price': sdt.today_closing_price, 'turnover_rate': sdt.turnover_rate}
            plate_stocks.append(item)

    plate_stocks = sorted(plate_stocks, key=lambda stock: float(stock.get('increase_rate').replace('%', '')),
                          reverse=True)
    for i in plate_stocks:
        print i['stock_number'], i['stock_name'], i['increase_rate'], i['today_closing_price']
    print len(plate_stocks)
    print market_plate


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'查询某个板块所对应的股票')
    parser.add_argument(u'-m', action=u'store', dest='market_plate', required=True, help=u'需要查询的板块')
    parser.add_argument(u'-f', action=u'store_true', dest='filter_rh',
                        help=u'如果添加这个参数，则在结果里会过滤瑞华的客户')

    args = parser.parse_args()
    return args.market_plate, args.filter_rh

if __name__ == '__main__':
    market_plate, filter_rh = setup_argparse()
    if isinstance(market_plate, str):
        if platform.system() == 'Windows':
            market_plate = market_plate.decode('gb2312')
        else:
            market_plate = market_plate.decode('utf-8')
    main(market_plate, filter_rh)
