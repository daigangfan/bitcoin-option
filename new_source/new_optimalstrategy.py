import numpy as np 
import pandas as pd 
import statsmodels.api as sts
from math import log ,sqrt,exp
from scipy.stats import norm 
from collections import OrderedDict
from datetime import datetime 
price_result = pd.read_excel("new_data/price_result.xlsx")
filtered_result = pd.read_excel("new_data/filtered_price_result.xlsx")

price_grouped = price_result.groupby("contract_label")
btc_data = pd.read_excel("new_data/btc_data.xlsx")


price_result_grouped = price_result.groupby("contract_label")
diff=price_result_grouped["vwap"].diff()
btc_data["btc_price_diff"]=btc_data["Price"].diff()
filtered_result["option_price_diff"]=diff
filtered_result["btc_price_diff"]=pd.merge(left=price_result,right=btc_data[["Date","btc_price_diff"]],left_on="date",right_on="Date",how="left")["btc_price_diff"]
def get_vega(x,ints=0.05):
    spot_price=x["spot_price"]
    strike_price=x["strike"]
    time=x["time"]/365
    volatility=x["volatility"]*sqrt(365)
    d1 = (log(spot_price/strike_price)+ints*time) /\
        (volatility*sqrt(time))+0.5*(volatility*sqrt(time))
    result=spot_price*norm.pdf(d1)*sqrt(time)
    return result
filtered_result["vega"]=filtered_result.apply(get_vega,axis=1)

# regression function
def reg(y,x):
    y=np.array(y)
    x=np.array(x)
    x=np.c_[x,x**2]
    x=sts.add_constant(x)
    
    model=sts.OLS(y,x,missing="drop")
    result=model.fit()
    return result

def roll(price_result):
    y=(price_result["option_price_diff"]-price_result["const_delta_5"]*price_result["btc_price_diff"])
    x=price_result["const_delta_5"]   
    result=reg(y,x)
    x=np.c_[np.ones(600),price_result.loc[:,"const_delta_5"],price_result.loc[:,"const_delta_5"]**2]
    return result.predict(x)

data=roll(filtered_result)
filtered_result["delta2"]=data
filtered_result["delta2"]=filtered_result["delta2"]/filtered_result["btc_price_diff"]
price_grouped = price_result.groupby("contract_label")

filtered_grouped = filtered_result.groupby("contract_label")

def get_spot_price(x):
    date1 = x
    return float(btc_data.query("Date==@date1")["Price"])

# 获得对冲交易的现金流


def trade_delta(x: pd.DataFrame, add_gamma=False):
    stream = OrderedDict()
    # 逐天开始
    for ind in range(x.shape[0]):
        cash = 0
        x_copy = x.iloc[ind].copy()
        try:
            check_data = filtered_grouped.get_group(
                x_copy["contract_label"])
        except KeyError:
            continue
        if not(check_data.date == x_copy.date).any():
            continue
        date=x_copy.date
        x_copy=check_data.query("date==@date").iloc[0]
        delta = x_copy["const_delta_5"]+x_copy["delta2"]
        weights = delta
        # 倒数第二条之前
        if ind+1 < x.shape[0] and x.iloc[ind+1]["date"] <= datetime(2018, 12, 31):
            # 实际价格低于模型价格，买入期权
            if x_copy["vwap"] < x_copy["int5"]:
                money = - x_copy["vwap"] +\
                    weights*x_copy["spot_price"]
                stream[x_copy["date"]]=money
                # 结束时平仓
                btc_spot_next = x.iloc[ind+1]["spot_price"]
                date_range=(x.iloc[ind+1]["date"]-x_copy["date"]).days
                stream[x.iloc[ind+1]["date"]] = x.iloc[ind +
                                                       1]["vwap"]-weights*btc_spot_next+0.05/365*date_range*money
            # 实际价格高于模型价格，卖出期权
            if x_copy["vwap"] > x_copy["int5"]:
                money = -weights * x_copy["spot_price"]+x_copy["vwap"]  
                stream[x_copy["date"]]=money
                # 结束时平仓
                date_range=(x.iloc[ind+1]["date"]-x_copy["date"]).days
                btc_spot_next = x.iloc[ind+1]["spot_price"]
                stream[x.iloc[ind+1]["date"]] = x.iloc[ind +
                                                       1]["vwap"]-weights*btc_spot_next+0.05/365*date_range*money

        # 最后一条,且在行权日之前
        if ind == x.shape[0]-1 and x.iloc[ind]["date"] < x.iloc[ind]["exp_date"] and x.iloc[ind]["exp_date"] <= datetime(2018, 12, 31):
            if x_copy["vwap"] < x_copy["int5"]:
                money= -x_copy["vwap"] + \
                    weights*x_copy["spot_price"]
                stream[x_copy["date"]] =money
                # 行权日
                btc_spot_next = get_spot_price(x_copy["exp_date"])
                date_range=(x_copy["exp_date"]-x_copy["date"]).days
                if x_copy["contract_is_call"]:
                    if btc_spot_next > x_copy["strike"]:  # 行权
                        stream[x_copy["exp_date"]] = - x_copy["strike"] + (1 - weights) * btc_spot_next+money*date_range*0.05/365

                    if btc_spot_next <= x_copy["strike"]:  # 不行权
                        stream[x_copy["exp_date"]] = - weights * btc_spot_next+money*date_range*0.05/365
                elif not x_copy["contract_is_call"]:
                    if btc_spot_next < x_copy["strike"]:  # 行权
                        stream[x_copy["exp_date"]] = x_copy["strike"] - \
                            btc_spot_next - weights * btc_spot_next+money*date_range*0.05/365

                    if btc_spot_next >= x_copy["strike"]:
                        stream[x_copy["exp_date"]] = - weights * btc_spot_next+money*date_range*0.05/365
            if x_copy["vwap"] > x_copy["int5"]:
                money= x_copy["vwap"] - \
                    weights * x_copy["spot_price"]
                stream[x_copy["date"]] =money
                # 行权日
                btc_spot_next = get_spot_price(x_copy["exp_date"])
                date_range=(x_copy["exp_date"]-x_copy["date"]).days
                if x_copy["contract_is_call"]:
                    if btc_spot_next > x_copy["strike"]:  # 行权
                        stream[x_copy["exp_date"]] = x_copy["strike"] - \
                            (1 - weights) * btc_spot_next+money*date_range*0.05/365

                    if btc_spot_next <= x_copy["strike"]:  # 不行权
                        stream[x_copy["exp_date"]] = cash + \
                            weights * btc_spot_next+money*date_range*0.05/365

                elif not x_copy["contract_is_call"]:
                    if btc_spot_next < x_copy["strike"]:  # 行权
                        stream[x_copy["exp_date"]] = - x_copy["strike"] + \
                            btc_spot_next + weights * btc_spot_next+money*date_range*0.05/365


                    if btc_spot_next >= x_copy["strike"]:
                        stream[x_copy["exp_date"]] = weights * btc_spot_next+money*date_range*0.05/365


    return stream


results = price_grouped.apply(trade_delta)

def get_return(x: OrderedDict):
    if len(x) == 0:
        return np.nan
    final_date = list(x.keys())[-1]
    start_date = list(x.keys())[0]
    net_in = 0
    net_out = 0
    for key, item in x.items():
        if item > 0:
            net_in += exp(-0.05*(final_date-key).days/365)*item
        if item <= 0:
            net_out += exp(-0.05*(final_date-key).days/365)*abs(item)
    range1 = (final_date-start_date).days
    return (((net_in-net_out))/range1)*365


returns = results.apply(get_return)
returns = returns.dropna()
call_returns = returns.loc[returns.index.str.contains("Call")]
put_returns = returns.loc[returns.index.str.contains("Put")]

with open("drift/new_describes/call_opt_return_describe.tex", "w") as f:
    f.write(call_returns.describe().to_latex())
with open("drift/new_describes/put_opt_return_describe.tex", "w") as f:
    f.write(put_returns.describe().to_latex())
