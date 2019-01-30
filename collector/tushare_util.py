#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'fengweigang'

import tushare
import config


def get_pro_client():
    return tushare.pro_api(config.tushare_token)


def get_daily_trading(date):
    return get_pro_client().daily(date)

