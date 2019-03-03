import statsmodels
import pandas as pd
import numpy as np

price_result = pd.read_excel("price_result.xlsx")
btc_data = pd.read_excel("btc_data.xlsx")


def match_skew(x):
    date = x
    used_data = btc_data.query("Date==@date")
    return used_data.iloc[0]["skewness"]


def match_kurt(x):
    date = x
    used_data = btc_data.query("Date==@date")
    return used_data.iloc[0]["kurtosis"]


price_result["btc_skew"] = price_result["date"].apply(match_skew)

price_result["btc_kurt"] = price_result["date"].apply(match_kurt)

