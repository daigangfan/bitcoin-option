# 用于生成描述性统计表格
import datetime

import pandas as pd

from math import isnan

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

# TODO: 更改行列名，添加附注
with open("describe_btc_data.tex", "w") as f:
    f.write(btc_describe.to_latex(float_format="{:.2f}".format))

option_initial_data = price_result.groupby("contract_label").first()

# TODO:对期限的统计是否有意义，因为第一条数据未必是发行日，存在大量期限为1的数据
option_describe = option_initial_data[["time", "strike"]].describe()

option_describe.loc["count", "call_number"] = 165
option_describe.loc["count", "put_number"] = 91

# TODO:更改行列名，添加附注
with open("describe_option_data.tex", "w") as f:
    f.write(option_describe.to_latex(
        float_format=lambda x: "{:.2f}".format(x) if not isnan(x) else " "))

writer = pd.ExcelWriter("price_result.xlsx")
with writer:
    price_result.to_excel(writer)

# TODO:分组统计的数据分组方式是否合理。
price_result["time_cut"] = pd.cut(
    price_result["time"], [0, 20, 80, 180, 637], right=False)
price_result["moneyness_cut"] = pd.cut(
    price_result["S/X"], [0, 0.6, 0.8, 1.2, 3.8], right=False)

price_biases = price_result.filter(regex="bias_int\d+", axis=1)
price_result[["abs_bias_int5", "abs_bias_int10", "abs_bias_int20",
              "abs_bias_int30"]] = price_biases.applymap(lambda x: abs(x))

price_result_grouped = price_result.groupby(["time_cut", "moneyness_cut"])

bias_int5_mean = price_result_grouped["bias_int5"].mean()
abs_bias_int5_mean = price_result_grouped["abs_bias_int5"].mean()

bias_int5_mean = bias_int5_mean.unstack("time_cut")
abs_bias_int5_mean = abs_bias_int5_mean.unstack("time_cut")


def reformat_index(x: pd.DataFrame):
    x.index = [str(a) for a in x.index]
    x.index.name = "moneyness_cut"
    x.columns = [str(a) for a in x.columns]
    x.columns.name = "time_cut"


reformat_index(bias_int5_mean)
reformat_index(abs_bias_int5_mean)

# TODO:原分组统计中大组的均值统计有问题。
time_cut_mean = price_result.groupby("time_cut")["bias_int5"].mean()
moneyness_cut_mean = price_result.groupby("moneyness_cut")["bias_int5"].mean()

time_cut_mean.index = [str(a) for a in time_cut_mean.index]
moneyness_cut_mean.index = [str(a) for a in moneyness_cut_mean.index]

bias_int5_mean.loc["mean"] = time_cut_mean
bias_int5_mean["mean"] = moneyness_cut_mean


time_cut_mean = price_result.groupby("time_cut")["abs_bias_int5"].mean()
moneyness_cut_mean = price_result.groupby(
    "moneyness_cut")["abs_bias_int5"].mean()

time_cut_mean.index = [str(a) for a in time_cut_mean.index]
moneyness_cut_mean.index = [str(a) for a in moneyness_cut_mean.index]

abs_bias_int5_mean.loc["mean"] = time_cut_mean
abs_bias_int5_mean["mean"] = moneyness_cut_mean

# TODO:更改行列名，添加附注
with open("option_bias_group.latex", "w") as f:
    f.write(bias_int5_mean.to_latex(float_format=lambda x: "{:.2f}".format(
        x) if not isnan(x) else " " ))

# TODO:更改行列名，添加附注
with open("option_abs_bias_group.latex", "w") as f:
    f.write(abs_bias_int5_mean.to_latex(
        float_format=lambda x: "{:.2f}".format(x) if not isnan(x) else " " ))
