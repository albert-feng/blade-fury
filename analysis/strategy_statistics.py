#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import platform

import pandas as pd
from pandas import DataFrame
from mongoengine import Q

from models import QuantResult as QR


back_test_attr = ['one_back_test', 'three_back_test', 'five_back_test']


def strategy_statistics(strategy_name):
    all_qr = QR.objects(strategy_name=strategy_name)

    if not all_qr:
        print 'Wrong Strategy Name!'
        return

    all_date = []
    for i in all_qr:
        if i.date not in all_date:
            all_date.append(i.date)

    all_date.sort()
    bt_result = {}
    for d in all_date:
        bt_result[str(d.date())] = back_test_success(strategy_name, d)

    frame = DataFrame(bt_result)
    print frame.reindex(['one_back_test', 'three_back_test', 'five_back_test']).T



def back_test_success(strategy_name, date):
    cursor = QR.objects(Q(strategy_name=strategy_name) & Q(date=date))

    res_by_date = {}
    for i in back_test_attr:
        qualified_sample = [qr[i] for qr in cursor if qr[i] is not None]
        if not qualified_sample:
            continue

        succ_sample = [q for q in qualified_sample if q is True]
        res_by_date[i] = str(round(float(len(succ_sample))/float(len(qualified_sample)), 4) * 100) + '%'

    return res_by_date


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'查询某个策略的回测统计结果')
    parser.add_argument(u'-s', action=u'store', dest='strategy_name', required=True, help=u'策略名')
    args = parser.parse_args()
    return args.strategy_name


if __name__ == '__main__':
    strategy_name = setup_argparse()
    strategy_statistics(strategy_name)
