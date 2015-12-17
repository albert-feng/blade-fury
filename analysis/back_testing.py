#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from mongoengine import Q

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT


test_pattern = {
                    1: {'test': 'one_back_test', 'price': 'one_price'},
                    3: {'test': 'three_back_test', 'price': 'three_price'},
                    5: {'test': 'five_back_test', 'price': 'five_price'},
                }


def test_by_day(qr, day):
    if isinstance(qr, QR):
        sdt = SDT.objects(Q(stock_number=qr.stock_number) & Q(date__gt=qr.date)).order_by('date')

        if sdt.count() >= day:
            back_test_sdt = sdt[day-1]
            qr[test_pattern[day]['price']] = back_test_sdt.today_closing_price
            price_spread = back_test_sdt.today_closing_price - qr.init_price

            if qr.strategy_direction == 'long':
                if price_spread >= 0:
                    qr[test_pattern[day]['test']] = True
                else:
                    qr[test_pattern[day]['test']] = False
            elif qr.strategy_direction == 'short':
                if price_spread > 0:
                    qr[test_pattern[day]['test']] = False
                else:
                    qr[test_pattern[day]['test']] = True

            qr.save()


def back_testing():
    quant_result = QR.objects()

    for i in quant_result:
        for t in test_pattern:
            if i[test_pattern[t]['test']] is None and i[test_pattern[t]['price']] is None:
                try:
                    test_by_day(i, t)
                except Exception, e:
                    logging.error('Error occur when back testing %s: %s' % (i.stock_number, e))


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    back_testing()
