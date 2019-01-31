#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'fengweigang'

import tushare
import config


def get_pro_client():
    return tushare.pro_api(config.tushare_token)

def gen_ts_code(stock_number):
    for i in config.ts_code_pattern:
        for n in i.get('pattern'):
            if stock_number.startswith(n):
                return stock_number + i.get('code_postfix')

