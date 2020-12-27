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
from config import f10_core_content, f9_survey, exchange_market, stock_value_url
from logger import setup_logging
from collector.collect_data_util import send_request


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
    query_id = stock_info.stock_number + estimate_market(stock_info.stock_number)

    company_survey_url = f9_survey.format(query_id)
    retry = 5
    survey_table = ''

    while retry:
        try:
            survey_html = send_request(company_survey_url)
            survey_soup = BeautifulSoup(survey_html, 'lxml')
            survey_table = survey_soup.find('table', id='tablefont').find_all('td')
            break
        except Exception as e:
            retry -= 1
            time.sleep(1)

    if not survey_soup or not survey_table:
        return

    stock_info.company_name_cn = survey_table[1].text.strip()
    stock_info.company_name_en = survey_table[3].text.strip()
    stock_info.used_name = survey_table[5].text.strip()
    stock_info.account_firm = survey_table[43].text.strip()
    stock_info.law_firm = survey_table[45].text.strip()
    stock_info.industry_involved = survey_table[17].text.strip()
    stock_info.business_scope = survey_table[47].text.strip()
    stock_info.company_introduce = survey_table[7].text.strip()
    stock_info.area = survey_table[25].text.strip()

    core_concept_url = f10_core_content.format(estimate_market(stock_info.stock_number, 'market') + stock_info.stock_number)
    concept_data = send_request(core_concept_url)
    try:
        concept_json = json.loads(concept_data)
        if concept_json.get('hxtc'):
            market_plate = concept_json.get('hxtc')[0].get('ydnr', '')
            stock_info.market_plate = market_plate
    except Exception as e:
        logging.error('parse concept data error, e = ' + str(e))
        pass

    stock_value_req = send_request(stock_value_url.format(estimate_market(stock_info.stock_number, 'value_code') +
                                                      stock_info.stock_number))
    try:
        stock_value_json = json.loads(stock_value_req)
        if stock_value_json.get('data') and stock_value_json.get('data').get('diff'):
            stock_value_datas = stock_value_json.get('data').get('diff')
            for i in range(len(stock_value_datas)):
                if stock_value_datas[i].get('f12') and stock_value_datas[i].get('f12') == stock_info.stock_number:
                    stock_value_info = stock_value_datas[i]
                    break

            stock_info.pe = stock_value_info.get('f9')
            stock_info.pb = stock_value_info.get('f23')
            stock_info.total_value = stock_value_info.get('f20')

    except Exception as e:
        logging.error('parse stock value fail: e = ' + str(e))

    stock_info.update_time = datetime.datetime.now()
    stock_info.save()


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
