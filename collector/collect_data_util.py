#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import time

import requests
from mongoengine import Q
from playwright.sync_api import sync_playwright

from models import StockDailyTrading as SDT
from models import StockWeeklyTrading as SWT


timeout = 30
default_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,zh-TW;q=0.4',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/46.0.2490.86 Safari/537.36'
    }


def send_request(url, headers={}):
    if headers:
        default_headers.update(headers)

    try:
        r = requests.get(url, headers=default_headers, timeout=timeout)
        r.encoding = 'utf-8'
    except Exception as e:
        logging.error('Request url %s failed: %s' % (url, e))
        raise e
    r.encoding = 'utf-8'
    html = r.text
    if not html:
        logging.warning('No data when request this url:' + url)
    return html


def fetch_page_content(url):
    with sync_playwright() as playwright:
        # 启动浏览器，headless=True 表示无头模式
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        # 等待页面加载完成
        page.wait_for_load_state('networkidle')
        # 获取页面内容
        content = page.content()
        browser.close()
        return content


def request_and_handle_data(url, headers={}):
    res = send_request(url, headers)

    try:
        data = json.loads(res.replace('var js=', '').replace('rank', '\"rank\"').replace('pages', '\"pages\"'))
    except Exception as e:
        logging.error('Handle data failed:' + str(e))
        raise e

    return data


def check_duplicate(trading_data):
    if isinstance(trading_data, SDT):
        cursor = SDT.objects(Q(stock_number=trading_data.stock_number) & Q(date=trading_data.date))
        if cursor:
            return True
        else:
            return False
    elif isinstance(trading_data, SWT):
        cursor = SWT.objects(Q(stock_number=trading_data.stock_number) &
                             Q(first_trade_date=trading_data.first_trade_date))
        if cursor:
            return True
        else:
            return False
