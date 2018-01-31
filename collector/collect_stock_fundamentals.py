#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'fengweigang'

'''
采集股票基本面信息
'''

import logging
import datetime

import tushare as ts

from models import StockInfo
from logger import setup_logging


def start_collect_fundamentals():
    df_all_stock = ts.get_stock_basics()
    for i in range(len(df_all_stock)):
        df_stock = df_all_stock.iloc[i]
        if not int(df_stock['timeToMarket']):
            continue

        try:
            cursor = StockInfo.objects(stock_number=df_stock.name)
            if cursor:
                stock_info = cursor[0]
            else:
                stock_info = StockInfo()

            stock_info.update_time = datetime.datetime.now()
            stock_info.industry = df_stock['industry']
            stock_info.pe = float(df_stock['pe'])
            stock_info.liquid_assets = int(df_stock['liquidAssets'])
            stock_info.fixed_assets = int(df_stock['fixedAssets'])
            stock_info.reserved = int(df_stock['reserved'])
            stock_info.reserved_per_share = float(df_stock['reservedPerShare'])
            stock_info.esp = float(df_stock['esp'])
            stock_info.bvps = float(df_stock['bvps'])
            stock_info.pb = float(df_stock['pb'])
            stock_info.time_to_market = datetime.datetime.strptime(str(df_stock['timeToMarket']), '%Y%m%d')
            stock_info.undp = float(df_stock['undp'])
            stock_info.perundp = float(df_stock['perundp'])
            stock_info.rev = float(df_stock['rev'])
            stock_info.profit = float(df_stock['profit'])
            stock_info.gpr = float(df_stock['gpr'])
            stock_info.npr = float(df_stock['npr'])
            stock_info.holders = int(df_stock['holders'])

            stock_info.save()
        except Exception as e:
            logging.error('Error when collect stock %s fundamentals from tushare:%s' % (df_stock.name, str(e)))


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock detail info')
    start_collect_fundamentals()
    logging.info('Collect stock detail info Success')

