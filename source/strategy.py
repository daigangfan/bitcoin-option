import pandas as pd
from datetime import datetime, timedelta
from math import sqrt, log, exp
import numpy as np
import scipy.stats as stats
from collections import OrderedDict
from dateutil.rrule import rrule, DAILY
price_result = pd.read_excel("data/price_result.xlsx")
filtered_result = pd.read_excel("data/filtered_price_result.xlsx")

filtered_grouped = filtered_result.groupby("contract_label")
btc_data = pd.read_excel("data/btc_data.xlsx")


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
    return (((net_in-net_out))/range1)*365


returns = results.apply(get_return)
returns = returns.dropna()
call_returns = returns.loc[returns.index.str.contains("Call")]
put_returns = returns.loc[returns.index.str.contains("Put")]
writer = pd.ExcelWriter("data/returns_plainBS.xlsx")
with writer:
    call_returns.to_excel(writer, sheet_name="call",index=False)
    put_returns.to_excel(writer, sheet_name="put",index=False)

with open("drift/call_return_describe.tex", "w") as f:
    f.write(call_returns.describe().to_latex())
with open("drift/put_return_describe.tex", "w") as f:
    f.write(put_returns.describe().to_latex())


def get_delta(spot_price, strike_price, time, option_type, volatility, ints=0.05):

    d1 = (log(spot_price/strike_price)+ints*time) /\
        (volatility*sqrt(time))+0.5*(volatility*sqrt(time))

    if option_type:
        return stats.norm.cdf(d1)
    else:
        return stats.norm.cdf(d1)-1


# reset a btc data use date as index
btc_date_data = btc_data.copy()
btc_date_data.index = btc_data["Date"]


def hedge_single(x: pd.Series, ints=0.05):
    expire_price = btc_date_data.loc[x["exp_date"], "Price"]
    strike = x["strike"]
    used_btc_data = btc_date_data.loc[x["date"]:x["exp_date"]]

    if x["contract_is_call"]:

        end_pay = max(expire_price-strike, 0)
    else:
        end_pay = max(strike-expire_price, 0)
    start_cost = x["vwap"]
    spot_change = used_btc_data["Price"].shift(-1)-used_btc_data["Price"]
    spot_change = spot_change.iloc[:-1]
    # 获得delta
    all_delta = []

    for date in rrule(DAILY, dtstart=x["date"], until=x["exp_date"]-timedelta(days=1)):
        spot = btc_date_data.loc[date, "Price"]
        time = ((x["exp_date"]-date).days+1)/sqrt(365)
        volatility = btc_date_data.loc[date, "volatility"]*sqrt(365)
        delta = get_delta(spot, strike, time,
                          x["contract_is_call"], volatility)
        all_delta.append(delta)
    delta_series = pd.Series(all_delta, index=spot_change.index)
    time_series = delta_series.reset_index().index
    hedge_cost = (delta_series*spot_change).sum()

    interest_cost = (ints*(x["vwap"]-delta_series *
                           used_btc_data["Price"].iloc[:-1])*time_series/365/x["time"]).sum()
    if x["vwap"] < x["int5"]:
        return end_pay-start_cost-hedge_cost-interest_cost
    else:
        return start_cost+hedge_cost+interest_cost-end_pay

### test


def trade_continuous(x: pd.DataFrame):
    result= x.apply(hedge_single,axis=1)
    result.index=x["date"]
    return result

#部分数据的到期日在此之后
end_date=datetime(2019,3,4)
new_filtered=filtered_result.query("exp_date<=@end_date")

x=new_filtered.loc[new_filtered.date==datetime(2017,12,17),:].iloc[0]
hedge_single(x)

new_filtered_grouped=new_filtered.groupby("contract_label")
continuous_result=new_filtered_grouped.apply(trade_continuous)
writer=pd.ExcelWriter("data/BS_continuous_hedge.xlsx")

call_part=continuous_result.filter(like="Call")
put_part=continuous_result.filter(like="Put")
with writer:
    call_part.to_excel(writer,sheet_name="call",index=False)
    put_part.to_excel(writer,sheet_name="put",index=False)
with open("drift/call_continuous_return_describe.tex","w") as f:
    f.write(call_part.describe().to_latex())
with open("drift/put_continuous_return_describe.tex","w") as f:
    f.write(put_part.describe().to_latex())