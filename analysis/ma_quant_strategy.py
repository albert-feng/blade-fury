#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
根据均线系统来进行选股
"""


from models import StockDailyTrading as SDT


def quant_stock(stock_number, stock_name, short_ma=5, long_ma=30):
    sdt = SDT.objects(stock_number=stock_number).order_by('-date')

    if sdt.count < long_ma + 5:
        """
        如果交易数据不够，跳过
        """
        return
    if float(sdt[0].increase_rate.replace('%', '')) == 0.0 and float(sdt[0].turnover_rate.replace('%', '')) == 0.0:
        """
        如果最新一天股票的状态是停牌，跳过
        """
        return

    # 计算出连续3个交易日长MA和短MA的值
    short_ma_list = []
    long_ma_list = []




if __name__ == '__main__':
    quant_stock(u'000547', u'航天发展')

