#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'fengweigang'

import config
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
    update_time = DateTimeField(default=datetime.datetime.now)
    company_name_cn = StringField(max_length=100)  # 公司中文名
    company_name_en = StringField(max_length=100)  # 公司英文名
    account_firm = StringField(max_length=100)  # 会计师事务所
    law_firm = StringField(max_length=100)  # 律师事务所
    industry_involved = StringField(max_length=100)  # 公司所属行业
    market_plate = ListField()  # 股票所属的板块
    business_scope = StringField(max_length=500)  # 公司经营范围
    company_introduce = StringField(max_length=1000)  # 公司简介
    area = StringField(max_length=20)  # 公司所在区域


