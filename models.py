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
    market_plate = ListField()  # 股票所属的板块
    business_scope = StringField()  # 公司经营范围
    company_introduce = StringField()  # 公司简介
    area = StringField(max_length=20)  # 公司所在区域


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
