from datetime import datetime
from math import log, sqrt, exp

import pandas as pd
from scipy.stats import norm

option_data = pd.read_excel("data/ledgerx_data.xlsx")
btc_data = pd.read_excel("data/btc_data.xlsx")

# TODO:波动率的计算，用`rolling`的方式包含今日，是否合适？
btc_data["volatility"] = btc_data["log_ret"].rolling(30).std()

# TODO:波动率窗口的选择（如何确定30天窗口是比较好的？）


def get_volatility(x):
    start_date = x
    data_used = btc_data.query("Date==@start_date")
    return data_used["volatility"].values[0]


def get_spot_price(x):
    date = x
    data_used = btc_data.query("Date==@date")
    return data_used["Price"].values[0]


option_data["volatility"] = option_data["date"].apply(get_volatility)
option_data["spot_price"] = option_data["date"].apply(get_spot_price)

# TODO:年化利率的选择，包括如何选择后面研究用到的利率（怎么从5，10，20 30）中选择的？


def Pricing(x, ints=0.05):
    maturity_date = x["exp_date"]
    start_date = x["date"]
    time = ((maturity_date - start_date).days + 1) / 365
    if time > 0:

        spot_price = x["spot_price"]
        strike_price = x["strike"]
        volatility = x["volatility"] * sqrt(365)
        d1 = (log(spot_price / strike_price) + ints * time) / (volatility * sqrt(time)) + 0.5 * (
            volatility * sqrt(time))
        d2 = (log(spot_price / strike_price) + ints * time) / (volatility * sqrt(time)) - 0.5 * (
            volatility * sqrt(time))
        if x["optiontype"].lower() == "call":
            price = spot_price * \
                norm.cdf(d1) - strike_price * exp(-ints * time) * norm.cdf(d2)
        if x["optiontype"].lower() == "put":
            price = strike_price * exp(-ints * time) * \
                norm.cdf(-d2) - spot_price * norm.cdf(-d1)
        return price
    else:
        return float("nan")


prices = pd.DataFrame()
prices["int5"] = option_data.apply(Pricing, axis=1, ints=0.05)
prices["int10"] = option_data.apply(Pricing, axis=1, ints=0.1)
prices["int20"] = option_data.apply(Pricing, axis=1, ints=0.2)
prices["int30"] = option_data.apply(Pricing, axis=1, ints=0.3)
price_result = pd.concat([option_data, prices], axis=1)

price_result["bias_int5"] = price_result["vwap"] - price_result["int5"]
price_result["bias_int10"] = price_result["vwap"] - price_result["int10"]
price_result["bias_int20"] = price_result["vwap"] - price_result["int20"]
price_result["bias_int30"] = price_result["vwap"] - price_result["int30"]


def check_bound(x, r=0.05):
    price = x["vwap"]
    if x["contract_is_call"]:
        return price >= x["spot_price"]-x["strike"]*exp(-r*x["time"]/365) and price <= x["spot_price"]
    else:
        return price <= x["strike"] and price >= x["strike"]*exp(-r*x["time"]/365)-x["spot_price"]


price_result["is_inbound"] = price_result.apply(check_bound,axis=1)

writer = pd.ExcelWriter("data/price_result.xlsx")
with writer:
    price_result.to_excel(writer)

writer = pd.ExcelWriter("data/btc_data.xlsx")
with writer:
    btc_data.to_excel(writer)
