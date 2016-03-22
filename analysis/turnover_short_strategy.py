#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging

from mongoengine import Q

from logger import setup_logging
from models import StockDailyTrading as SDT, QuantResult as QR


def is_duplicate(stock_number, date, strategy_name):
    try:
        cursor = QR.objects(Q(stock_number=stock_number) & Q(date=date) & Q(strategy_name=strategy_name))
    except Exception, e:
        logging.error('Query %s QR failed:%s' % (stock_number, e))

    if cursor:
        return True
    else:
        return False


def quant_stock():
    today = datetime.date.today()
    increase_rate = '6%'
    quantity_relative_ratio = 3
    try:
        sdt = SDT.objects(Q(date=today) & Q(increase_rate__gte=increase_rate) &
                          Q(quantity_relative_ratio__gte=quantity_relative_ratio))
    except Exception, e:
        logging.error('Query DB failed:%s' % e)
        raise e

    for i in sdt:
        strategy_name = 'turnover_short'
        qr = QR()
        qr.stock_number = i.stock_number
        qr.stock_name = i.stock_name
        qr.date = i.date
        qr.strategy_direction = 'short'
        qr.strategy_name = strategy_name
        qr.init_price = i.today_closing_price

        try:
            if not is_duplicate(i.stock_number, i.date, strategy_name):
                qr.save()
        except Exception, e:
            logging.error('Save %s quant result failed:%s' % (i.stock_number, e))


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    quant_stock()
