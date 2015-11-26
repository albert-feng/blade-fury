#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'fengweigang'

import random
import time
import datetime
import logging

import requests
from bs4 import BeautifulSoup

from models import StockInfo
from config import core_concept, company_survey, exchange_market
from logger import setup_logging


timeout = 30


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
        'Host': 'f10.eastmoney.com',
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
    survey_table = survey_soup.find('table', id='Table0').find_all('td')
    stock_info.company_name_cn = survey_table[0].text
    stock_info.company_name_en = survey_table[1].text
    stock_info.account_firm = survey_table[30].text
    stock_info.law_firm = survey_table[29].text
    stock_info.industry_involved = survey_table[10].text
    stock_info.business_scope = survey_table[32].text
    stock_info.company_introduce = survey_table[31].text
    stock_info.area = survey_table[23].text

    core_concept_url = core_concept.format(query_id)
    concept_html = send_request(core_concept_url)
    concept_soup = BeautifulSoup(concept_html, 'lxml').find('div', class_='summary').find('p').text
    stock_info.market_plate = concept_soup.replace(u'要点一：所属板块　', '').replace(u'。', '').split(u'，')
    stock_info.update_time = datetime.datetime.now()
    stock_info.save()


def start_collect_detail():
    try:
        all_stocks = StockInfo.objects().timeout(False)
    except Exception, e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    for i in all_stocks:
        try:
            collect_company_survey(i)
        except Exception, e:
            logging.error('Error when collect %s data: %s' % (i.stock_number, e))
        time.sleep(random.random())


if __name__ == '__main__':
    setup_logging(__file__)
    start_collect_detail()
