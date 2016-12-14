#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging

import pandas as pd
from pandas import DataFrame
from mongoengine import Q

from models import QuantResult as QR
from models import StockDailyTrading as SDT
from models import StockInfo
from logger import setup_logging







