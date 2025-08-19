#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
author: albert feng
description: 周线策略差异分析 - 比较当天与前一天的选股结果，找出新增的股票
"""

import datetime
import logging
import argparse

from mongoengine import Q

from logger import setup_logging
from models import QuantResult as QR, StockWeeklyTrading as SWT

from analysis.technical_analysis_util import start_quant_analysis, check_duplicate_strategy


def quant_stock(stock_number, stock_name, **kwargs):
    """
    核心量化逻辑：比较当天与前一天的策略结果，找出新增的选股
    """
    strategy_name = kwargs['strategy_name']
    qr_date = kwargs['qr_date']

    # 检查是否是星期一，如果是则返回
    if qr_date.weekday() == 0:  # 0表示星期一
        return

    # 检查当天是否有该策略的量化结果
    today_results = QR.objects(Q(strategy_name=strategy_name) & Q(date=qr_date))
    if not today_results:
        return

    # 获取qr_date的前一天
    previous_date = qr_date - datetime.timedelta(days=1)

    # 查询包含qr_date和前一天的周线数据
    current_week = SWT.objects(Q(stock_number=stock_number) & Q(first_trade_date__lte=qr_date) & Q(last_trade_date__gte=qr_date)).first()
    previous_week = SWT.objects(Q(stock_number=stock_number) & Q(first_trade_date__lte=previous_date) & Q(last_trade_date__gte=previous_date)).first()

    if not current_week or not previous_week:
        return

    # 检查是否是同一周的K线数据
    if current_week.first_trade_date != previous_week.first_trade_date:
        return

    # 查询上一个交易日的量化结果
    previous_results = QR.objects(Q(strategy_name=strategy_name) & Q(date=previous_date))

    # 获取当天和前一天的股票编号集合
    today_stocks = set([result.stock_number for result in today_results])
    previous_stocks = set([result.stock_number for result in previous_results])

    # 找出新增的股票（当天有但前一天没有的）
    new_stocks = today_stocks - previous_stocks

    # 如果当前股票是新增的，则保存到量化结果中
    if stock_number in new_stocks:
        # 获取当天该股票的原始量化结果
        original_result = today_results.filter(stock_number=stock_number).first()
        if original_result:
            # 创建新的量化结果，策略名称加上_diff后缀
            diff_strategy_name = strategy_name + '_diff'

            qr = QR(
                stock_number=stock_number,
                stock_name=stock_name,
                date=qr_date,
                strategy_direction=original_result.strategy_direction,
                strategy_name=diff_strategy_name,
                init_price=original_result.init_price,
                industry_involved=kwargs.get('industry_involved'),
                increase_rate=original_result.increase_rate
            )

            if not check_duplicate_strategy(qr):
                qr.save()
                return qr

    return


def setup_argparse():
    """
    设置命令行参数解析
    """
    parser = argparse.ArgumentParser(description=u'周线策略差异分析 - 比较当天与前一天的选股结果差异')
    parser.add_argument(u'-s', action=u'store', dest='strategy_name', required=True, help=u'策略名称')
    parser.add_argument(u'-t', action=u'store', dest='qr_date', required=False, help=u'分析日期')
    args = parser.parse_args()

    if args.qr_date:
        try:
            qr_date = datetime.datetime.strptime(args.qr_date, '%Y-%m-%d')
        except Exception as e:
            print('Wrong date format, should be YYYY-MM-DD')
            raise e
    else:
        today = datetime.date.today()
        qr_date = datetime.datetime(year=today.year, month=today.month, day=today.day)

    return args.strategy_name, qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    strategy_name, qr_date = setup_argparse()

    real_time_res = start_quant_analysis(
        strategy_name=strategy_name,
        qr_date=qr_date,
        quant_stock=quant_stock
    )
