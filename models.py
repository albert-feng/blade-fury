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
    stock_number = StringField(primary_key=True, required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
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
    total_value = IntField() #  公司总市值
    circulated_value = IntField() #  公司流通市值
    meta = {
        'indexes': ['#stock_number', '#stock_name', '$market_plate'],
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
    date = DateTimeField(default=datetime.date.today())  # 收录股票交易数据的日期
    timestamp = IntField(default=int(time.time()))  # 收录数据时的时间戳
    meta = {
        'indexes': ['date', 'quantity_relative_ratio', '#stock_number'],
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
        'indexes': ['date', '#index_number'],
        'index_background': True,
    }


class StockMinTrading(Document):
    """
    存储股票交易分钟线数据
    """

    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
    bar = IntField(required=True, choices=config.min_bar)  # 分钟线级别
    bar_time = DateTimeField(required=True)  # 分钟线起始时间
    close_price = FloatField(required=True)  # 分钟线结束价格
    open_price = FloatField(required=True)  # 分钟线开始价格
    high_price = FloatField(required=True)  # 分钟线最高价
    low_price = FloatField(required=True)  # 分钟线最低价


class StockNotice(Document):
    """
    存放股票公告信息
    """

    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
    notice_title = StringField()  # 公告标题
    notice_cate = StringField()  # 公告类型
    notice_date = DateTimeField()  # 公告日期
    notice_url = StringField()  # 公告URL
    notice_content = StringField()  # 公告正文
    meta = {
        'indexes': ['notice_date', '#stock_number'],
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
    init_price = FloatField()  # 选出股票时这个票的收盘价
    one_back_test = BooleanField()  # 一个交易日之后的回测结果
    one_price = FloatField()  # 一个交易日之后回测时的价格
    three_back_test = BooleanField()  # 三个交易日之后的回测结果
    three_price = FloatField()  # 三个交易日之后回测时的价格
    five_back_test = BooleanField()  # 五个交易日之后的回测结果
    five_price = FloatField()  # 五个交易日之后的价格
    meta = {
        'indexes': ['date', '#stock_number', '#strategy_name'],
        'index_background': True,
    }


class ResearchReport(Document):
    """
    存放研究报告数据
    """
    stock_number = StringField(required=True, max_length=10)  # 股票编号
    stock_name = StringField(required=True, max_length=20)  # 股票名称
    date = DateTimeField(required=True)  # 研究报告发布的日期
    title = StringField(required=True)  # 评级的机构
    author = StringField()  # 作者
    rate_change = StringField(max_length=10)  # 研究报告的评级变化
    rate = StringField(max_length=10)  # 研究报告的评级
    institution = StringField(required=True, max_length=20)  # 评级的机构
    content = StringField()  # 评级报告的内容
    meta = {
        'indexes': ['date', '#stock_number'],
        'index_background': True,
    }


class BuffettIndex(Document):
    """
    用来计算每天的总市值/上一年度GDP的值
    """
    date = DateTimeField(required=True)  # 计算巴菲特指标的日期
    total_value = FloatField(required=True)  # 存储当天的a股总市值，单位：万亿
    buffett_index = StringField(required=True)  # 存储当天计算的巴菲特指标
    meta = {
        'indexes': ['date'],
        'index_background': True,
    }


if __name__ == '__main__':
    StockInfo.ensure_indexes()
    StockNotice.ensure_indexes()
    StockDailyTrading.ensure_indexes()
    QuantResult.ensure_indexes()
    BuffettIndex.ensure_indexes()
    IndexDailyTrading.ensure_indexes()
