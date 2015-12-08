#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 使用mongodb存储数据
mongodb_config = {
    'host': 'localhost',
    'port': 27017,
    'db': 'blade_fury',
}

# 数据都是从东财爬的...
eastmoney_stock_api = 'http://hqdigi2.eastmoney.com/EM_Quote2010NumericApplication/index.aspx?type=s&sortType=C'\
                      '&sortRule=-1&style=33&pageSize=3000&page=1'
core_concept = 'http://f10.eastmoney.com/f10_v2/CoreConception.aspx?code={}'
company_survey = 'http://f10.eastmoney.com/f10_v2/CompanySurvey.aspx?code={}'
company_accouncement = 'http://data.eastmoney.com/Notice/NoticeStock.aspx?type=0&stockcode={}&pn=1'
eastmoney_data = 'http://data.eastmoney.com'
rzrq_sh = 'http://data.eastmoney.com/rzrq/sh.html'
rzrq_sz = 'http://data.eastmoney.com/rzrq/sz.html'
rzrq_tital = 'http://data.eastmoney.com/rzrq/total.html'

exchange_market = [{'market': 'sh', 'pattern': ['60']}, {'market': 'sz', 'pattern': ['00', '30']}]

log_path = '/data/log/blade-fury.log'
local_log_path = 'blade-fury.log'
