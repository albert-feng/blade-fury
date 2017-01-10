#!/usr/bin/env python
# -*- coding: utf-8 -*-


from pandas import DataFrame


def calculate_macd(df, short_ema, long_ema, dif_ema):
    if isinstance(df, DataFrame):
        df = df.set_index(['date'])
        df['short_ema'] = df['price'].ewm(span=short_ema).mean()
        df['long_ema'] = df['price'].ewm(span=long_ema).mean()
        df['dif'] = df['short_ema'] - df['long_ema']
        df['dea'] = df['dif'].ewm(span=dif_ema).mean()
        df['macd'] = df['dif'] - df['dea']
        return df
    else:
        raise Exception('df type is wrong')


def calculate_ma(df, short_ma, long_ma):
    if isinstance(df, DataFrame):
        df = df.set_index(['date'])
        df['short_ma'] = df['price'].rolling(window=short_ma, center=False).mean()
        df['long_ma'] = df['price'].rolling(window=long_ma, center=False).mean()
        df['diff_ma'] = df['short_ma'] - df['long_ma']
        return df
    else:
        raise Exception('df type is wrong')
