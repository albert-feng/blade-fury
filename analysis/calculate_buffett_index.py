#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import datetime

from logger import setup_logging
from models import StockInfo, BuffettIndex, StockDailyTrading as SDT

GDP = 67.67


def total_market_value():
    cursor = StockInfo.objects()
    total_value = 0.0
    for i in cursor:
        if u'退市' not in i.stock_name and isinstance(i.total_value, int):
            total_value += float(i.total_value)

    trillion = 10.0 ** 12
    return round(total_value/trillion, 4)


def save_data():
    global GDP
    total_value = total_market_value()
    buffett_index = str(round(total_value/GDP, 6) * 100) + '%'
    bi = BuffettIndex(date=datetime.date.today(), buffett_index=buffett_index, total_value=total_value)
    try:
        bi.save()
    except Exception, e:
        logging.error('Error when save BuffettIndex data:' + str(e))


def cal_buffett_index():
    today = datetime.date.today()
    sdt = SDT.objects(date=today)
    if not sdt:
        return

    bi = BuffettIndex.objects(date=today)
    if bi:
        return

    save_data()


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    cal_buffett_index()
