# 用于生成描述性统计表格
import datetime

import pandas as pd

price_result = pd.read_excel("price_result.xlsx")
price_result["S/X"] = price_result["spot_price"] / price_result["strike"]
btc_data = pd.read_excel("btc_data.xlsx")


def get_time(x):
    start_time = x["date"]
    end_time = x["exp_date"]
    return (end_time - start_time).days + 1


price_result["time"] = price_result.apply(get_time, axis=1)

btc_data["skewness"] = btc_data["log_ret"].rolling(30).skew()
btc_data["kurtosis"] = btc_data["log_ret"].rolling(30).kurt()


def fix_price(x):
    return float(x.replace(",", ""))


btc_data["Price"] = btc_data["Price"].apply(fix_price)

start_time = datetime.datetime(2017, 10, 17)
btc_data = btc_data.query("Date>@start_time")
btc_describe = btc_data.describe()
btc_describe.loc["count"] = btc_describe.loc["count"].astype(int)
with open("describe_btc_data.tex", "w") as f:
    f.write(btc_describe.to_latex(float_format="{:.2f}".format))

option_initial_data = price_result.groupby("contract_label").first()

option_describe = option_initial_data[["time", "strike"]].describe()

option_describe.loc["count", "call_number"] = 165
option_describe.loc["count", "put_number"] = 91

with open("describe_option_data.tex", "w") as f:
    f.write(option_describe.to_latex(float_format="{:.2f}".format))

writer = pd.ExcelWriter("price_result.xlsx")
with writer:
    price_result.to_excel(writer)

price_result["time_cut"] = pd.cut(
    price_result["time"], [0, 20, 80, 180, 637], right=False)
price_result["strike_cut"] = pd.cut(
    price_result["strike"], [0, 0.6, 0.8, 1.2, 3.79], right=False)

price_biases = price_result.filter(regex="bias_int\d+", axis=1)
price_result[["abs_bias_int5", "abs_bias_int10", "abs_bias_int20",
              "abs_bias_int30"]] = price_biases.applymap(lambda x: abs(x))
