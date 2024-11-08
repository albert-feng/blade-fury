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

from bs4 import BeautifulSoup

from models import StockInfo
from config import f10_core_content, f9_survey, exchange_market, stock_value_url, stock_basic_info, f9_info
from logger import setup_logging
from collector.collect_data_util import send_request, fetch_page_content


query_step = 100  # 每次查询数据库的步长，以防出现cursor超时的错误


def estimate_market(stock_number, attr='code'):
    market = ''
    for i in exchange_market:
        if stock_number[0] in i.get('pattern'):
            market = i.get(attr)
            break

    if not market:
        raise Exception('Wrong stock number %s' % stock_number)
    return market


def collect_company_survey(stock_info):
    query_id = estimate_market(stock_info.stock_number, 'market') + stock_info.stock_number

    company_survey_url = stock_basic_info.format(query_id)
    retry = 5
    survey_table = ''

    while retry:
        try:
            survey_html = fetch_page_content(company_survey_url)
            survey_soup = BeautifulSoup(survey_html, 'lxml')
            survey_table = survey_soup.find('div', class_='jbzl_table').find_all('tr')
            break
        except Exception as e:
            retry -= 1
            time.sleep(1)

    if not survey_soup or not survey_table:
        return

    stock_info.company_name_cn = survey_table[0].find('td').text.strip()
    stock_info.company_name_en = survey_table[1].find('td').text.strip()
    stock_info.used_name = survey_table[3].find_all('td')[-1].text.strip()
    stock_info.account_firm = survey_table[17].find_all('td')[-1].text.strip()
    stock_info.law_firm = survey_table[17].find_all('td')[0].text.strip()
    stock_info.industry_involved = survey_table[6].find_all('td')[-1].text.strip()
    stock_info.business_scope = survey_table[19].find('td').text.strip()
    stock_info.company_introduce = survey_table[18].find('td').text.strip()
    stock_info.area = survey_table[14].find_all('td')[0].text.strip()

    core_concept_url = f9_info.format(query_id)
    
    try:
        f9_stock_info = fetch_page_content(core_concept_url)
        f9_soup = BeautifulSoup(f9_stock_info, 'lxml')
        hxtc_info = f9_soup.find('div', id='hxtc_content')
        
        market_plate = hxtc_info.find_all('p')[0].text.strip().replace('要点一:  ', '').replace('所属板块', '')
        stock_info.market_plate = market_plate
    except Exception as e:
        logging.error('parse concept data error, e = ' + str(e))
        pass

    try:
        stock_info.save()
    except Exception as e:
        logging.error('save stock detail data error, e = ' + str(e))
        pass


def start_collect_detail():
    try:
        all_stocks = StockInfo.objects()
    except Exception as e:
        logging.error('Error when query StockInfo:' + str(e))
        raise e

    stocks_count = len(all_stocks)
    skip = 0

    while skip < stocks_count:
        try:
            stocks = StockInfo.objects().skip(skip).limit(query_step)
        except Exception as e:
            logging.error('Error when query skip %s  StockInfo:%s' % (skip, e))
            stocks = []

        for i in stocks:
            try:
                collect_company_survey(i)
            except Exception as e:
                logging.error('Error when collect %s data: %s' % (i.stock_number, e))
            time.sleep(random.random())
        skip += query_step


if __name__ == '__main__':
    setup_logging(__file__, logging.WARNING)
    logging.info('Start to collect stock detail info')
    start_collect_detail()
    logging.info('Collect stock detail info Success')
