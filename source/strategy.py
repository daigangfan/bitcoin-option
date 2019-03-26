import pandas as pd
from datetime import datetime
from math import sqrt, log, exp
import numpy as np
import scipy.stats as stats
from collections import OrderedDict

price_result = pd.read_excel("data/price_result.xlsx")
filtered_result = pd.read_excel("data/filtered_price_result.xlsx")

filtered_grouped = filtered_result.groupby("contract_label")
btc_data = pd.read_excel("data/btc_data.xlsx")


def get_BS_delta(x, ints=0.05):
    spot_price = x["spot_price"]
    strike_price = x["strike"]
    ints = 0.05
    maturity_date = x["exp_date"]
    start_date = x["date"]
    time = ((maturity_date-start_date).days+1)/365
    option_type = x["contract_is_call"]
    volatility = x["volatility"]*sqrt(365)
    d1 = (log(spot_price/strike_price)+ints*time) /\
        (volatility*sqrt(time))+0.5*(volatility*sqrt(time))

    if option_type == "Call":
        return stats.norm.cdf(d1)
    else:
        return stats.norm.cdf(d1)-1


price_result_grouped = price_result.groupby("contract_label")
# 获得指定日期的比特币现价


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
        delta = x_copy["delta_5"]
        weights = delta
        # 倒数第二条之前
        if ind+1 < x.shape[0] and x.iloc[ind+1]["date"] <= datetime(2018, 12, 31):
            # 实际价格低于模型价格，买入期权
            if x_copy["vwap"] < x_copy["int5"]:
                stream[x_copy["date"]] = - x_copy["vwap"] +\
                    weights*x_copy["spot_price"]
                # 结束时平仓
                btc_spot_next = x.iloc[ind+1]["spot_price"]
                stream[x.iloc[ind+1]["date"]] = x.iloc[ind +
                                                       1]["vwap"]-weights*btc_spot_next
            # 实际价格高于模型价格，卖出期权
            if x_copy["vwap"] > x_copy["int5"]:
                stream[x_copy["date"]] = weights * \
                    x_copy["spot_price"]-x_copy["vwap"]  # 结束时平仓
                btc_spot_next = x.iloc[ind+1]["spot_price"]
                stream[x.iloc[ind+1]["date"]] = x.iloc[ind +
                                                       1]["vwap"]-weights*btc_spot_next

        # 最后一条,且在行权日之前
        if ind == x.shape[0]-1 and x.iloc[ind]["date"] < x.iloc[ind]["exp_date"] and x.iloc[ind]["exp_date"] <= datetime(2018, 12, 31):
            if x_copy["vwap"] < x_copy["int5"]:
                stream[x_copy["date"]] = -x_copy["vwap"] + \
                    weights*x_copy["spot_price"]

                # 行权日
                btc_spot_next = get_spot_price(x_copy["exp_date"])
                if x_copy["contract_is_call"]:
                    if btc_spot_next > x_copy["strike"]:  # 行权
                        stream[x_copy["exp_date"]] = cash - \
                            x_copy["strike"] + (1 - weights) * btc_spot_next

                    if btc_spot_next <= x_copy["strike"]:  # 不行权
                        stream[x_copy["exp_date"]] = - weights * btc_spot_next
                elif not x_copy["contract_is_call"]:
                    if btc_spot_next < x_copy["strike"]:  # 行权
                        stream[x_copy["exp_date"]] = x_copy["strike"] - \
                            btc_spot_next - weights * btc_spot_next

                    if btc_spot_next >= x_copy["strike"]:
                        stream[x_copy["exp_date"]] = - weights * btc_spot_next
            if x_copy["vwap"] > x_copy["int5"]:
                stream[x_copy["date"]] = x_copy["vwap"] - \
                    weights * x_copy["spot_price"]
                # 行权日
                btc_spot_next = get_spot_price(x_copy["exp_date"])
                if x_copy["contract_is_call"]:
                    if btc_spot_next > x_copy["strike"]:  # 行权
                        stream[x_copy["exp_date"]] = x_copy["strike"] - \
                            (1 - weights) * btc_spot_next
                    if btc_spot_next <= x_copy["strike"]:  # 不行权
                        stream[x_copy["exp_date"]] = cash + \
                            weights * btc_spot_next
                elif not x_copy["contract_is_call"]:
                    if btc_spot_next < x_copy["strike"]:  # 行权
                        stream[x_copy["exp_date"]] = - x_copy["strike"] + \
                            btc_spot_next + weights * btc_spot_next

                    if btc_spot_next >= x_copy["strike"]:
                        stream[x_copy["exp_date"]] = weights * btc_spot_next

    return stream


results = price_result_grouped.apply(trade_delta)


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
    return (((net_in-net_out)/net_out)/range1)*365


returns = results.apply(get_return)
returns = returns.dropna()
call_returns = returns.loc[returns.index.str.contains("Call")]
put_returns = returns.loc[returns.index.str.contains("Put")]
writer = pd.ExcelWriter("data/returns_plainBS.xlsx")
with writer:
    call_returns.to_excel(writer, sheet_name="call")
    put_returns.to_excel(writer, sheet_name="put")

with open("drift/call_return_describe.tex", "w") as f:
    f.write(call_returns.describe().to_latex())
with open("drift/put_return_describe.tex", "w") as f:
    f.write(put_returns.describe().to_latex())

