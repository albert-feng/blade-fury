#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import logging
from os.path import dirname, join, exists

from config import log_path, local_log_path


def setup_logging(file=__file__, level=logging.INFO):
    try:
        if not exists(dirname(log_path)):
            os.mkdirs(dirname(log_path))
        logging.basicConfig(
            filename=log_path,
            level=level,
            filemode='a',
            format='%(asctime)s ' + file + ' - %(levelname)s: %(message)s',
        )
    except Exception:
        print('Setup Default log failed...')
        print('Setup log in blade-fury')
        log_local = join(dirname(__file__), local_log_path)
        logging.basicConfig(
            filename=log_local,
            level=level,
            filemode='a',
            format='%(asctime)s ' + file + ' - %(levelname)s: %(message)s',
        )
