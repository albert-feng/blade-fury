#!/usr/bin/env python
# -*- coding: utf-8 -*-

import config
import time
import datetime
from mongoengine import *

db = config.mongodb_config['db']
connect(db)


class StockInfo(Document):
    """
    存储股票及其公司的本身的信息
    """
    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(max_length=20)  # 股票名称
    used_name = StringField()  # 曾用名
    create_time = DateTimeField(default=datetime.datetime.now)
    update_time = DateTimeField()
    company_name_cn = StringField(max_length=100)  # 公司中文名
    company_name_en = StringField(max_length=100)  # 公司英文名
    account_firm = StringField(max_length=100)  # 会计师事务所
    law_firm = StringField(max_length=100)  # 律师事务所
    industry_involved = StringField(max_length=100)  # 公司所属行业
    market_plate = StringField()  # 股票所属的板块
    business_scope = StringField()  # 公司经营范围
    company_introduce = StringField()  # 公司简介
    area = StringField(max_length=20)  # 公司所在区域
    total_value = IntField(default=0)  # 公司总市值
    circulated_value = IntField(default=0)  # 公司流通市值
    meta = {
        'indexes': ['stock_number'],
        'index_background': True,
    }


class StockDailyTrading(Document):
    """
    存储股票每天的交易数据，包括价格，成交等信息
    """

    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
    yesterday_closed_price = FloatField()  # 昨日收盘价 单位 rmb
    today_opening_price = FloatField()  # 今日开盘价 单位 rmb
    today_closing_price = FloatField()  # 今日收盘价 单位 rmb
    today_highest_price = FloatField()  # 今日最高价 单位 rmb
    today_lowest_price = FloatField()  # 今日最低价 单位 rmb
    turnover_amount = IntField()  # 成交额 单位 /万
    turnover_volume = IntField()  # 成交量 单位 /手
    increase_amount = FloatField()  # 股票今日上涨额 单位 rmb
    increase_rate = StringField()  # 股票今日涨幅 单位 %
    today_average_price = FloatField()  # 股票今日平均价格 单位 rmb
    quantity_relative_ratio = FloatField()  # 股票今日量比
    turnover_rate = StringField()  # 股票今日换手率
    total_stock = IntField()  # 股票的当日总股本
    circulation_stock = IntField()  # 股票的当日流通股
    date = DateTimeField(default=datetime.date.today())  # 收录股票交易数据的日期
    timestamp = IntField(default=int(time.time()))  # 收录数据时的时间戳
    year_ma = FloatField(default=0)  # 年线价格 单位 rmb
    meta = {
        'indexes': ['date', 'stock_number', 'today_closing_price', ('stock_number', '-date'), ('stock_number', 'date')],
        'index_background': True,
    }


class StockWeeklyTrading(Document):
    """
    存储股票周线数据
    """

    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
    first_trade_date = DateTimeField(required=True)  # 首个交易日
    last_trade_date = DateTimeField(required=True)  # 最后交易日
    end_date = DateTimeField(required=True)  # 截止日期
    trade_days = IntField()  # 交易天数
    pre_close_price = FloatField()  # 昨收价
    weekly_open_price = FloatField()  # 开盘价
    weekly_close_price = FloatField()  # 收盘价
    weekly_highest_price = FloatField()  # 最高价
    weekly_lowest_price = FloatField()  # 最低价
    weekly_avg_price = FloatField()  # 成交均价
    ad_open_price = FloatField()  # 后复权开盘价
    ad_close_price = FloatField()  # 后复权收盘价
    ad_highest_price = FloatField()  # 后复权最高价
    ad_lowest_price = FloatField()  # 后复权最低价
    range_percent = StringField()  # 振幅 单位 %
    increase_rate = StringField()  # 涨幅 单位 %
    turnover_amount = IntField()  # 成交额 单位 /万
    turnover_volume = IntField()  # 成交量 单位 /手
    meta = {
        'indexes': ['stock_number', 'last_trade_date', ('stock_number', 'last_trade_date'),
                    ('stock_number', '-last_trade_date'), ('stock_number', 'first_trade_date'),
                    ('stock_number', '-first_trade_date')],
        'index_background': True,
    }


class IndexDailyTrading(Document):
    """
    存储每天的指数交易数据
    """

    index_number = StringField(required=True)  # 指数编号
    index_name = StringField(required=True)  # 指数名称
    yesterday_closed_point = FloatField()  # 昨日收盘点数
    today_opening_point = FloatField()  # 今日开盘点数
    today_closing_point = FloatField()  # 今日收盘点数
    today_highest_point = FloatField()  # 今日最高点数
    today_lowest_point = FloatField()  # 今日最低点数
    turnover_amount = IntField()  # 成交额 单位 /万
    turnover_volume = IntField()  # 成交量 单位 /手
    increase_point = FloatField()  # 上涨的点数
    increase_rate = StringField()  # 指数的涨幅
    date = DateTimeField(default=datetime.date.today())  # 收录指数交易数据的日期
    timestamp = IntField(default=int(time.time()))  # 收录指数数据时的时间戳
    meta = {
        'indexes': ['date', 'index_number'],
        'index_background': True,
    }


class StockNotice(Document):
    """
    存放股票公告信息
    """

    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
    title = StringField()  # 公告标题
    code = StringField()
    date = DateTimeField()  # 公告日期
    content_url = StringField()  # 公告URL
    meta = {
        'indexes': ['date', 'stock_number', 'code', ('stock_number', '-date')],
        'index_background': True,
    }


class StockMarginTrading(Document):
    """
    存储股票的两融情况
    """
    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
    date = DateTimeField(default=datetime.date.today())  # 收录股票两融数据的日期
    rz_remaining_amount = StringField()  # 融资余额 单位 rmb
    rz_buy_amount = StringField()  # 融资买入额 单位 rmb
    rz_repay_amount = StringField()  # 融资偿还额 单位 rmb
    rz_net_buy_amount = StringField()  # 融资净买入额 单位 rmb
    rq_remaining_volume = StringField()  # 融券余量 单位 股
    rq_sell_volume = StringField()  # 融券卖出量 单位 股
    rq_repay_volume = StringField()  # 融券偿还量 单位 股


class QuantResult(Document):
    """
    由量化分析选出的股票
    """
    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
    date = DateTimeField(default=datetime.date.today())  # 根据相应策略选出股票的日期
    strategy_direction = StringField(choices=['long', 'short'], default='long')  # 策略的方向性，可以是做多和做空
    strategy_name = StringField()  # 策略的名称
    industry_involved = StringField(max_length=100)  # 公司所属行业
    init_price = FloatField()  # 选出股票时这个票的收盘价
    increase_rate = FloatField()  # 股票今日涨幅 单位 %
    one_back_test = BooleanField()  # 一个交易日之后的回测结果
    one_price = FloatField()  # 一个交易日之后回测时的价格
    three_back_test = BooleanField()  # 三个交易日之后的回测结果
    three_price = FloatField()  # 三个交易日之后回测时的价格
    five_back_test = BooleanField()  # 五个交易日之后的回测结果
    five_price = FloatField()  # 五个交易日之后的价格
    ten_back_test = BooleanField()  # 十个交易日之后的回测结果
    ten_price = FloatField()  # 十个交易日之后的价格
    meta = {
        'indexes': ['date', ('strategy_name', 'date'), ('strategy_name', '-date')],
        'index_background': True,
    }


class StockReport(Document):
    """
    存放研究报告数据
    """
    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
    date = DateTimeField(required=True)  # 研究报告发布的日期
    info_code = StringField()  # 报告的东财ID
    title = StringField(required=True)  # 评级的机构
    author = StringField()  # 作者
    rate_change = StringField(max_length=10)  # 研究报告的评级变化
    rate = StringField(max_length=10)  # 研究报告的评级
    institution = StringField(required=True, max_length=20)  # 评级的机构
    content = StringField()  # 评级报告的内容
    meta = {
        'indexes': ['date', 'stock_number'],
        'index_background': True,
    }


class ShareHolder(Document):
    """
    存放前10大股东信息
    """
    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
    is_total = BooleanField()  # 标识是否全体股东统计 True: 全部股份 False: 流通股
    date = DateTimeField(required=True)  # 研究报告发布的日期
    share_holder_name = StringField()  # 股东名称
    share_amount = IntField()  # 股东持股数
    share_percent = FloatField()  # 持股比例
    share_change = StringField()  # 变化
    share_type = StringField()  # 股份类型：A股，H股


if __name__ == '__main__':
    StockInfo.ensure_indexes()
    StockNotice.ensure_indexes()
    StockDailyTrading.ensure_indexes()
    StockWeeklyTrading.ensure_indexes()
    QuantResult.ensure_indexes()
    IndexDailyTrading.ensure_indexes()
    StockReport.ensure_indexes()
