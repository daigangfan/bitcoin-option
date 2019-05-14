import datetime

import pandas as pd

from math import isnan

import numpy as np 
import matplotlib.pyplot as plt 
plt.style.use("classic")
plt.rcParams["font.sans-serif"]=["SimHei"]
price_result = pd.read_excel("new_data/price_result.xlsx")
price_result["S/X"] = price_result["spot_price"] / price_result["strike"]
btc_data = pd.read_excel("new_data/btc_data.xlsx")


btc_data["skewness"] = btc_data["log_ret"].rolling(365).skew()
btc_data["kurtosis"] = btc_data["log_ret"].rolling(365).kurt()

btc_data["amihud"]=np.abs(btc_data["log_ret"])/np.log(btc_data["Volume"])
btc_data["amihud"]=btc_data["amihud"].rolling(30,min_periods=1).sum()


start_time = datetime.datetime(2017, 10, 17)
btc_data = btc_data.query("Date>=@start_time")

#画波动率图
figure=plt.figure()
ax=figure.add_subplot(111)
ax.plot(btc_data["Date"],btc_data["volatility"]*np.sqrt(365)*100,"--",label="波动率")
ax.set_xlabel("时间")
ax.set_ylabel("年化波动率(%)")
ax2=ax.twinx()
ax2.set_ylabel("比特币价格(美元)")
ax2.plot(btc_data["Date"],btc_data["Price"],"-",label="价格")
line1,label1=ax.get_legend_handles_labels()
line2,label2=ax2.get_legend_handles_labels()
ax2.legend(line1+line2,label1+label2)
for lab in ax.get_xticklabels():
    lab.set_rotation(30)
plt.savefig("drift/figures/volatility.png",bbox_inches="tight",dpi=800)


btc_describe = btc_data.describe()
btc_describe.loc["count"] = btc_describe.loc["count"].astype(int)
btc_describe=btc_describe[["Volume","log_ret","volatility","skewness","kurtosis"]]

btc_describe.rename(columns={
    "Volume":"成交量",
    "log_ret":"对数收益率",
    "volatility":"波动率",
    "skewness":"偏度",
    "kurtosis":"峰度"
},inplace=True)


with open("drift/new_describes/describe_btc_data.tex", "w",encoding="utf-8") as f:
    f.write(btc_describe.to_latex(float_format="{:.3f}".format))

option_initial_data = price_result.groupby("contract_label").first()


option_describe = option_initial_data[["time", "strike"]].describe()

option_describe.loc["count", "call_number"] = option_initial_data["contract_is_call"].value_counts()[
    1]
option_describe.loc["count", "put_number"] = option_initial_data["contract_is_call"].value_counts()[
    0]
option_describe.rename(columns={
"time":"期限",
"strike":"行权价",
"call_number":"认购期权数量",
"put_number":"认沽期权数量"
},inplace=True)

# TODO:更改行列名，添加附注
with open("drift/new_describes/describe_option_data.tex", "w",encoding="utf-8") as f:
    f.write(option_describe.to_latex(
        float_format=lambda x: "{:.3f}".format(x) if not isnan(x) else " "))

writer = pd.ExcelWriter("new_data/price_result.xlsx")
with writer:
    price_result.to_excel(writer,index=False)

writer = pd.ExcelWriter("new_data/btc_data.xlsx")
with writer:
    btc_data.to_excel(writer,index=False)
