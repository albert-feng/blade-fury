#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

import pandas as pd
from pandas import DataFrame
from mongoengine import Q

from models import QuantResult as QR


back_test_attr = {'one_back_test': ['one_price', 'one_yield_expectation'],
                  'three_back_test': ['three_price', 'three_yield_expectation'],
                  'five_back_test': ['five_price', 'five_yield_expectation']}


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
    pd.set_option('display.width', 200)
    pd.set_option('display.max_rows', 200)
    print frame.reindex(['count', 'one_back_test', 'one_yield_expectation', 'three_back_test', 'three_yield_expectation',
                         'five_back_test', 'five_yield_expectation']).T
    pd.set_option('display.width', None)
    pd.set_option('display.max_rows', None)


def back_test_success(strategy_name, date):
    cursor = QR.objects(Q(strategy_name=strategy_name) & Q(date=date))

    res_by_date = {}
    for k, v in back_test_attr.iteritems():
        qualified_sample = [qr for qr in cursor if qr[k] is not None]
        if not qualified_sample:
            res_by_date['count'] = cursor.count()
            continue

        succ_sample = [q for q in qualified_sample if q[k] is True]
        res_by_date[k] = str(round(float(len(succ_sample))/float(len(qualified_sample)), 4) * 100) + '%'

        yield_expectation = 0.0
        if 'long' in strategy_name:
            for i in qualified_sample:
                yield_expectation += (i[v[0]] - i.init_price)/i.init_price
        elif 'short' in strategy_name:
            for i in qualified_sample:
                yield_expectation += (i.init_price - i[v[0]])/i.init_price

        res_by_date[v[1]] = str(round(yield_expectation/len(qualified_sample), 4) * 100) + '%'
        res_by_date['count'] = cursor.count()
    return res_by_date


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'查询某个策略的回测统计结果')
    parser.add_argument(u'-s', action=u'store', dest='strategy_name', required=True, help=u'策略名')
    args = parser.parse_args()
    return args.strategy_name


if __name__ == '__main__':
    strategy_name = setup_argparse()
    strategy_statistics(strategy_name)
