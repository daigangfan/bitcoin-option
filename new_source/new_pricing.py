from datetime import datetime
from math import log, sqrt, exp
import numpy as np
import pandas as pd
from scipy.stats import norm

option_data = pd.read_excel("new_data/ledgerx_data.xlsx")
btc_data = pd.read_excel("new_data/btc_data.xlsx")
btc_data.index=btc_data["Date"]
btc_data["volatility"] = btc_data["log_ret"].rolling(365).std()
btc_data["kurtosis"] = btc_data["log_ret"].rolling(365).kurt()
btc_data["skewness"] = btc_data["log_ret"].rolling(365).skew()
btc_data["amihud"]=np.abs(btc_data["log_ret"])/np.log(btc_data["Volume"])
btc_data["amihud"]=btc_data["amihud"].rolling(30,min_periods=1).sum()
start_time = datetime(2017, 10, 17)
used_btc_data = btc_data["20171017":"20190101"]

option_data["volatility"] = btc_data["volatility"].loc[option_data["date"]].values
option_data["spot_price"] = btc_data["Price"].loc[option_data["date"]].values

TOTAL_VOL=used_btc_data["log_ret"].std()
option_data["const_volatility"]=TOTAL_VOL
def Pricing(x, ints=0.05,const=True):
    maturity_date = x["exp_date"]
    start_date = x["date"]
    time = ((maturity_date - start_date).days + 1) / 365
    if time > 0:

        spot_price = x["spot_price"]
        strike_price = x["strike"]
        volatility = x["const_volatility"] * sqrt(365) if const else x["volatility"] * sqrt(365)
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
prices["const_int5"] = option_data.apply(Pricing, axis=1, ints=0.05)
prices["int5"]=option_data.apply(Pricing,axis=1,ints=0.05,const=False)

price_result = pd.concat([option_data, prices], axis=1)
price_result["const_bias"]=price_result["vwap"]/price_result["const_int5"]
price_result["bias"]=price_result["vwap"]/price_result["int5"]
price_result["S/X"]=price_result["spot_price"]/price_result["strike"]

def check_bound(x, r=0.05):
    price = x["vwap"]
    if x["contract_is_call"]:
        return price >= x["spot_price"]-x["strike"]*exp(-r*x["time"]/365) and price <= x["spot_price"]
    else:
        return price <= x["strike"] and price >= x["strike"]*exp(-r*x["time"]/365)-x["spot_price"]


price_result["is_inbound"] = price_result.apply(check_bound,axis=1)

# calculate delta 

def get_BS_delta(x, ints=0.05,const=True):
    spot_price = x["spot_price"]
    strike_price = x["strike"]
    time = x["time"]/365
    option_type = x["contract_is_call"]
    volatility = x["const_volatility"]*sqrt(365) if const else x["volatility"]*sqrt(365)
    d1 = (log(spot_price/strike_price)+ints*time) /\
        (volatility*sqrt(time))+0.5*(volatility*sqrt(time))

    if option_type:
        return norm.cdf(d1)
    else:
        return norm.cdf(d1)-1

price_result["const_delta_5"]=price_result.apply(get_BS_delta,axis=1)
price_result["delta_5"]=price_result.apply(get_BS_delta,axis=1,const=False)

writer = pd.ExcelWriter("new_data/price_result.xlsx")
with writer:
    price_result.to_excel(writer,index=False)

writer = pd.ExcelWriter("new_data/btc_data.xlsx")
with writer:
    btc_data.to_excel(writer,index=False)
