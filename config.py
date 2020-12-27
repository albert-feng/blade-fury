#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 使用mongodb存储数据
mongodb_config = {
    'host': 'localhost',
    'port': 27017,
    'db': 'blade_fury',
}

# 数据都是从东财爬的...
eastmoney_stock_api = 'http://hqdigi2.eastmoney.com/EM_Quote2010NumericApplication/index.aspx?type=s&sortType=C'\
                      '&sortRule=-1&style=33&pageSize=4000&page=1'
core_concept = 'http://f10.eastmoney.com/f10_v2/CoreConception.aspx?code={}'
company_survey = 'http://f10.eastmoney.com/f10_v2/CompanySurvey.aspx?code={}'

company_notice = 'http://data.eastmoney.com/notices/getdata.ashx?StockCode={}&CodeType=1&PageIndex=1&PageSize=100'
single_notice = 'http://data.eastmoney.com/notices/detail/{}/{},JUU0JUJBJTlBJUU3JThFJTlCJUU5JUExJUJG.html'

company_news = 'http://guba.eastmoney.com/list,{},1,f.html'
guba_domain = 'guba.eastmoney.com'

eastmoney_data = 'http://data.eastmoney.com'
# stock_value = 'http://nuff.eastmoney.com/EM_Finance2015TradeInterface/JS.ashx?id={}'
rzrq_sh = 'http://datainterface.eastmoney.com/EM_DataCenter/JS.aspx?type=FD&sty=MTND&mkt=1&st=C&sr=1&p=1&ps=2000'
rzrq_sz = 'http://datainterface.eastmoney.com/EM_DataCenter/JS.aspx?type=FD&sty=MTND&mkt=2&st=C&sr=1&p=1&ps=2000'
rzrq_api = [rzrq_sh, rzrq_sz]

history_trading = 'http://soft-f9.eastmoney.com/soft/gp9.php?code={}'

exchange_market = [{'market': 'sh', 'pattern': ['6'], 'cd': 'XSHG', 'code': '01', 'value_code': '1.'},
                   {'market': 'sz', 'pattern': ['0', '3'], 'cd': 'XSHE', 'code':'02', 'value_code': '0.'}]
f9_survey = 'http://f9.eastmoney.com/soft/gp3.php?color=b&code={}'
f9_core_content = 'http://f9.eastmoney.com/hxtc/GetCoreContent?stockcode={}'
f10_core_content = 'http://f10.eastmoney.com/CoreConception/CoreConceptionAjax?code={}'

log_path = '/data/log/blade-fury/blade-fury.log'
local_log_path = 'blade-fury.log'

company_report = 'http://datainterface.eastmoney.com/EM_DataCenter/js.aspx?type=SR&sty=GGSR&'\
                 'js={"data":[(x)],"pages":"(pc)","update":"(ud)","count":"(count)"}&ps=1000&p=1'
base_report_url = 'http://data.eastmoney.com/report/'

market_index = 'http://hqdigi2.eastmoney.com/EM_Quote2010NumericApplication/Index.aspx?type=z&sortType=C&sortRule=-1&'\
               'jsSort=1&ids=0000011,3990012,0003001,3990052,3990062,0009051,0000161&dt=1466650941761'

datayes_day_trading = 'https://api.wmcloud.com/data/v1/api/market/getMktEqud.json?tradeDate={}'
datayes_week_trading = 'https://api.wmcloud.com/data/v1/api/market/getMktEquw.json?ticker={}&beginDate={}&endDate={}&isOpen=1'
datayes_week_ad = 'https://api.wmcloud.com/data/v1/api/market/getMktEquwAdjAf.json?ticker={}&beginDate={}&endDate={}&isOpen=1'

datayes_headers = {'Authorization': 'Bearer 996149e6618da9316706120d1fff64c47265ed0e99e88c4897990d898918da92'}
stock_exchange = {u'上海': u'XSHG', u'深圳': u'XSHE'}

tushare_token = '6c0171c5179b008eedf3a32391be1ce08627e10684aa6215bc8edc28'
ts_code_pattern = [
    {'code_postfix': '.SH', 'pattern': ['6']},
    {'code_postfix': '.SZ', 'pattern': ['00', '30']}
]

stock_value_url = 'http://push2.eastmoney.com/api/qt/slist/get?spt=1&np=3&fltt=2&invt=2&fields=f9,f12,f13,f14,f20,' \
                  'f23,f37,f45,f49,f134,f135,f129&secid={}'
