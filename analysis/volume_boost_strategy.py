#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
author: albert feng
description: 成交量放大策略 - 获取股票最近10天的日线交易数据，去掉下跌的，
             如果当日交易量大于前一日交易量的2.5倍，或者大于前5日平均成交量的2倍，
             则将这只股票纳入策略选择结果
"""

import datetime
import logging
import argparse

from mongoengine import Q
from pandas import DataFrame

from logger import setup_logging
from models import QuantResult as QR, StockDailyTrading as SDT
from analysis.technical_analysis_util import check_duplicate_strategy
from analysis.technical_analysis_util import start_quant_analysis, pre_sdt_check


def quant_stock(stock_number, stock_name, **kwargs):
    """
    核心量化逻辑：成交量放大策略
    """
    qr_date = kwargs['qr_date']

    # 检查基础数据
    if not pre_sdt_check(stock_number, **kwargs):
        return

    # 获取最近10天的日线交易数据
    recent_data = SDT.objects(
        Q(stock_number=stock_number)
        & Q(today_closing_price__ne=0.0)
        & Q(date__lte=qr_date)
    ).order_by('-date')[:10]
    if len(recent_data) < 10:
        # 数据不足10天
        return

    # 转换为DataFrame并去掉下跌的数据
    df_data = []
    for record in recent_data:
        df_data.append({
            'date': record.date,
            'closing_price': record.today_closing_price,
            'opening_price': record.today_opening_price,
            'volume': record.volume,
            'stock_number': record.stock_number
        })

    df = DataFrame(df_data)

    # 去掉下跌的数据（收盘价低于开盘价）
    df = df[df['closing_price'] >= df['opening_price']]

    if len(df) < 2:
        # 去掉下跌数据后数据不足
        return

    # 获取当日数据（第一条数据）
    today_data = df.iloc[0]
    today_volume = today_data['volume']

    # 获取前一日数据
    yesterday_data = df.iloc[1]
    yesterday_volume = yesterday_data['volume']

    # 计算前5日平均成交量（排除今日）
    recent_5_days = df.iloc[1:6]  # 昨日及前4日
    if len(recent_5_days) >= 5:
        avg_5day_volume = recent_5_days['volume'].mean()
    else:
        # 如果不足5天，用可用数据计算
        avg_5day_volume = recent_5_days['volume'].mean()

    # 判断成交量条件
    volume_condition_1 = today_volume > (yesterday_volume * 2.5)  # 当日交易量 > 前一日交易量 * 2.5
    volume_condition_2 = today_volume > (avg_5day_volume * 2)    # 当日交易量 > 前5日平均成交量 * 2

    if volume_condition_1 or volume_condition_2:
        # 满足成交量放大条件，创建量化结果
        strategy_name = 'volume_boost'

        # 计算涨幅（相对于前一日收盘价）
        price_change_rate = (today_data['closing_price'] - yesterday_data['closing_price']) / yesterday_data['closing_price'] * 100

        qr = QR(
            stock_number=stock_number,
            stock_name=stock_name,
            date=qr_date,
            strategy_direction='long',  # 放量上涨看多
            strategy_name=strategy_name,
            init_price=today_data['closing_price'],
            industry_involved=kwargs.get('industry_involved'),
            increase_rate=price_change_rate
        )

        if not check_duplicate_strategy(qr):
            qr.save()
            return qr

    return


def setup_argparse():
    """
    设置命令行参数解析
    """
    parser = argparse.ArgumentParser(description=u'成交量放大策略 - 基于成交量异常放大的选股策略')
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

    return qr_date


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    qr_date = setup_argparse()

    real_time_res = start_quant_analysis(
        qr_date=qr_date,
        quant_stock=quant_stock
    )
