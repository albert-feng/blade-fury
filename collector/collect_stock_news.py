#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用来获取股票新闻，数据来自东财
"""

import random
import time
import datetime
import logging
import json
import chardet

import requests
from bs4 import BeautifulSoup
from mongoengine import Q

from models import StockInfo, StockNotice
from config import eastmoney_data, company_notice, single_notice
from logger import setup_logging


timeout = 30  # 发送http请求的超时时间
query_step = 30  # 一次从数据库中取出的数据量
