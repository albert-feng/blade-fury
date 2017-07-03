#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用来采集每天股票的两融情况
"""

import logging

import requests
from mongoengine import Q

from config import rzrq_api
from models import StockMarginTrading as SMT
from logger import setup_logging
from collector.collect_data_util import send_request


def collect_margin_trading(req_url):
    html = send_request(req_url)

    margin_data = eval(html)
    for i in margin_data:
        margin_item = i.decode('utf-8').split(',')
        stock_number = margin_item[0]
        stock_name = margin_item[2]
        rz_net_buy_amount = margin_item[3]
        rq_repay_volume = margin_item[5]
        rq_sell_volume = margin_item[6]
        rq_remaining_volume = margin_item[8]
        rz_repay_amount = margin_item[9]
        rz_buy_amount = margin_item[10]
        rz_remaining_amount = margin_item[12]
        smt = SMT(stock_number=stock_number, stock_name=stock_name, rz_net_buy_amount=rz_net_buy_amount,
                  rq_repay_volume=rq_repay_volume, rq_sell_volume=rq_sell_volume,
                  rq_remaining_volume=rq_remaining_volume, rz_repay_amount=rz_repay_amount,
                  rz_buy_amount=rz_buy_amount, rz_remaining_amount=rz_remaining_amount)

        if not is_duplicate(smt):
            smt.save()


def is_duplicate(smt):
    duplicate_data = SMT.objects(Q(stock_number=smt.stock_number) &
                                 Q(stock_name=smt.stock_name) &
                                 Q(rz_net_buy_amount=smt.rz_net_buy_amount) &
                                 Q(rq_repay_volume=smt.rq_repay_volume) &
                                 Q(rq_sell_volume=smt.rq_sell_volume) &
                                 Q(rq_remaining_volume=smt.rq_remaining_volume) &
                                 Q(rz_repay_amount=smt.rz_repay_amount) &
                                 Q(rz_buy_amount=smt.rz_buy_amount) &
                                 Q(rz_remaining_amount=smt.rz_remaining_amount))
    if duplicate_data:
        return True
    else:
        return False


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock margin trading')
    for url in rzrq_api:
        try:
            collect_margin_trading(url)
        except Exception as e:
            logging.error('Collect margin trading %s failed:%s' % (url, e))
    logging.info('collect stock margin trading success')
