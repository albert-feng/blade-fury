#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

import pandas as pd
from pandas import DataFrame
from mongoengine import Q

from models import QuantResult as QR


back_test_attr = {'one_back_test': ['one_price', 'one_yield'],
                  'three_back_test': ['three_price', 'three_yield'],
                  'five_back_test': ['five_price', 'five_yield'],
                  'ten_back_test': ['ten_price', 'ten_yield']
                  }


def strategy_statistics(strategy_name, strategy_count, stock_model=''):
    all_qr = QR.objects(strategy_name=strategy_name)
    if not all_qr:
        print 'Wrong Strategy Name!'
        return

    trading_date = QR.objects().distinct('date')
    trading_date.sort()
    trading_date = trading_date[0-strategy_count:]
    bt_result = {}
    for d in trading_date:
        bt_result[str(d.date())] = back_test_success(strategy_name, d, stock_model)

    frame = DataFrame(bt_result)
    pd.set_option('display.width', 200)
    pd.set_option('display.max_rows', strategy_count+100)
    print frame.reindex(['count', 'one_back_test', 'one_yield_expectation', 'three_back_test',
                         'three_yield_expectation', 'five_back_test', 'five_yield_expectation']).T
    pd.set_option('display.width', None)
    pd.set_option('display.max_rows', None)


def back_test_success(strategy_name, date, stock_model=''):
    if stock_model:
        cursor = QR.objects(Q(strategy_name=strategy_name) & Q(date=date) & Q(stock_number__startswith=stock_model))
    else:
        cursor = QR.objects(Q(strategy_name=strategy_name) & Q(date=date))

    res_by_date = {}
    for k, v in back_test_attr.iteritems():
        qualified_sample = [qr for qr in cursor if qr[k] is not None]
        if not qualified_sample:
            res_by_date['count'] = cursor.count()
            continue

        succ_sample = [q for q in qualified_sample if q[k] is True]
        res_by_date[k] = str(round(float(len(succ_sample))/float(len(qualified_sample)), 4) * 100) + '%'

        yield_exp = 0.0
        if 'long' in strategy_name:
            for i in qualified_sample:
                yield_exp += (i[v[0]] - i.init_price)/i.init_price
        elif 'short' in strategy_name:
            for i in qualified_sample:
                yield_exp += (i.init_price - i[v[0]])/i.init_price

        res_by_date[v[1]] = str(round(yield_exp/len(qualified_sample), 4) * 100) + '%'
        res_by_date['count'] = cursor.count()
    return res_by_date


def setup_argparse():
    parser = argparse.ArgumentParser(description=u'查询某个策略的回测统计结果')
    parser.add_argument(u'-s', action=u'store', dest='strategy_name', required=True, help=u'策略名')
    parser.add_argument(u'-c', action=u'store', type=int, dest='strategy_count', required=False, help=u'返回策略数')
    parser.add_argument(u'-m', action=u'store', dest='stock_model', required=False, help=u'匹配的股票类型')
    args = parser.parse_args()

    strategy_count = args.strategy_count
    if not strategy_count:
        strategy_count = 50
    stock_model = args.stock_model
    if not stock_model:
        stock_model = ''
    return args.strategy_name, strategy_count, stock_model


if __name__ == '__main__':
    strategy_name, strategy_count, stock_model = setup_argparse()
    strategy_statistics(strategy_name, strategy_count, stock_model)
