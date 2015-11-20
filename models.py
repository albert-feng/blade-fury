#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'fengweigang'

import config
import datetime
from mongoengine import *

db = config.mongodb_config['db']
connect(db)

class StockInfo(Document):
    """docstring for StockInfo"""

    stock_number = StringField(primary_key=True, required=True, max_length=10)
    stock_name = StringField(required=True, max_length=20)
    create_time = DateTimeField(default=datetime.datetime.now)
    update_time = DateTimeField(default=datetime.datetime.now)


