#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
这个脚本仅用来获取股票更多方面的信息
"""

import random
import time
import datetime
import logging
import json

import requests
from bs4 import BeautifulSoup

from models import StockInfo
from config import core_concept, company_survey, exchange_market, stock_value
from logger import setup_logging


timeout = 30  # 发送http请求时的超时时间
query_step = 100  # 每次查询数据库的步长，以防出现cursor超时的错误
concept_separator = [u'，', u' ']


def estimate_market(stock_number):
    market = ''
    for i in exchange_market:
        if stock_number[:2] in i.get('pattern'):
            market = i.get('market')
            break

    if not market:
        raise Exception('Wrong stock number %s' % stock_number)
    return market


def send_request(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36',
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    html = r.text
    if not html:
        logging.warning('No data when request this url:' + url)
    return html


def collect_company_survey(stock_info):
    query_id = estimate_market(stock_info.stock_number)+stock_info.stock_number

    company_survey_url = company_survey.format(query_id)
    survey_html = send_request(company_survey_url)
    survey_soup = BeautifulSoup(survey_html, 'lxml')
    stock_info.stock_name = survey_soup.find('p', class_='key').find('a').text.strip()
    survey_table = survey_soup.find('table', id='Table0').find_all('td')
    stock_info.company_name_cn = survey_table[0].text.strip()
    stock_info.company_name_en = survey_table[1].text.strip()
    stock_info.account_firm = survey_table[30].text.strip()
    stock_info.law_firm = survey_table[29].text.strip()
    stock_info.industry_involved = survey_table[10].text.strip()
    stock_info.business_scope = survey_table[32].text.strip()
    stock_info.company_introduce = survey_table[31].text.strip()
    stock_info.area = survey_table[23].text.strip()

    core_concept_url = core_concept.format(query_id)
    concept_html = send_request(core_concept_url)
    market_plate = BeautifulSoup(concept_html, 'lxml').find('div', class_='summary').find('p').text\
        .replace(u'要点一：所属板块　', '').replace(u'。', '').strip()
    stock_info.market_plate = market_plate

    if 'sh' in query_id:
        q_id = stock_info.stock_number + '1'
    elif 'sz' in query_id:
        q_id = stock_info.stock_number + '2'

    if q_id:
        stock_value_url = stock_value.format(q_id)
        try:
            res = send_request(stock_value_url)
            data = json.loads(res.replace('callback(', '').replace(')', ''))['Value']
            circulated_value = int(data[45])
            total_value = int(data[46])
            stock_info.circulated_value = circulated_value
            stock_info.total_value = total_value
        except Exception, e:
            logging.error('Error when get %s value:%s' % (stock_info.stock_number, e))

    stock_info.update_time = datetime.datetime.now()
    stock_info.save()


def start_collect_detail():
    try:
        all_stocks = StockInfo.objects()
    except Exception, e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    stocks_count = len(all_stocks)
    skip = 0

    while skip < stocks_count:
        try:
            stocks = StockInfo.objects().skip(skip).limit(query_step)
        except Exception, e:
            logging.error('Error when query skip %s  StockInfo:%s' % (skip, e))
            stocks = []

        for i in stocks:
            try:
                collect_company_survey(i)
            except Exception, e:
                logging.error('Error when collect %s data: %s' % (i.stock_number, e))
            time.sleep(random.random())
        skip += query_step


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock detail info')
    start_collect_detail()
    logging.info('Collect stock detail info Success')
