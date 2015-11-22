#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'fengweigang'


mongodb_config = {
    'host': 'localhost',
    'port': 27017,
    'db': 'blade_fury',
}

eastmoney_stock_api = 'http://hqdigi2.eastmoney.com/EM_Quote2010NumericApplication/index.aspx?type=s&sortType=C'\
                      '&sortRule=-1&style=33&pageSize=3000&page=1'
core_concept = 'http://f10.eastmoney.com/f10_v2/CoreConception.aspx?code={}'
company_survey = 'http://f10.eastmoney.com/f10_v2/CompanySurvey.aspx?code={}'

exchange_market = [{'market': 'sh', 'pattern': ['60']}, {'market': 'sz', 'pattern': ['00', '30']}]
