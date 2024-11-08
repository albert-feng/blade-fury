import os, sys
import unittest
from unittest.mock import patch, MagicMock
project_root = os.path.join(os.path.dirname(__file__) , '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from collector.collect_stock_detail_info import collect_company_survey


# 假设的 stock_info 类，用于测试
class MockStockInfo:
    def __init__(self):
        self.stock_number = '000002'
        self.company_name_cn = ''
        self.company_name_en = ''
        self.used_name = ''
        self.account_firm = ''
        self.law_firm = ''
        self.industry_involved = ''
        self.business_scope = ''
        self.company_introduce = ''
        self.area = ''
        self.market_plate = ''
        self.pe = ''
        self.pb = ''
        self.total_value = ''
        self.update_time = None

    def save(self):
        pass  # 在测试中不执行实际的保存操作


class TestCollectCompanySurvey(unittest.TestCase):

    def test_collect_company_survey(self):
        stock_info = MockStockInfo()

        # 运行待测函数
        collect_company_survey(stock_info)


if __name__ == '__main__':
    unittest.main()
