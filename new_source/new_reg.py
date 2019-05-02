
from statsmodels.iolib.summary2 import summary_col
import pandas as pd
import numpy as np
from imply_vol import calc_imp_vol
import datetime
import re
from math import log, exp, sqrt
from scipy.stats import norm
from statsmodels.formula import api as stf
import matplotlib.pyplot as plt

price_result = pd.read_excel("new_data/filtered_price_result.xlsx")
btc_data = pd.read_excel("new_data/btc_data.xlsx")
if "skewness" not in price_result.columns:
    price_result = pd.merge(left=price_result, right=btc_data[[
        "Date", "skewness", "kurtosis", "log_ret","Volume"]], left_on="date", right_on="Date", how="left")
    price_result.drop(columns=["Date"], inplace=True)

price_result["imply_vol"] = price_result.apply(calc_imp_vol, axis=1)
price_result["contract_is_call"] = price_result["contract_is_call"].astype(int)

def get_implied_vega(x, ints=0.05):
    spot_price = x["spot_price"]
    strike_price = x["strike"]
    time = x["time"]/365
    volatility = x["imply_vol"]
    d1 = (log(spot_price/strike_price)+ints*time) /\
        (volatility*sqrt(time))+0.5*(volatility*sqrt(time))
    result = spot_price*norm.pdf(d1)*sqrt(time)
    return result


price_result["imply_vega"] = price_result.apply(get_implied_vega, axis=1)


def get_weighted_ISD(x: pd.DataFrame):
    elasticity = x["imply_vega"]*x["imply_vol"]/x["vwap"]
    return (x["imply_vol"]*elasticity).sum()/elasticity.sum()

daily_weighted_ISD = price_result.groupby("date").apply(get_weighted_ISD)
btc_data.index = btc_data["Date"]
btc_data["weighted_ISD"] = daily_weighted_ISD

def get_vol_pre(x):
    start_date = x["date"]
    end_date = x["exp_date"]
    if x["time"] < 30:
        return x["imply_vol"]/np.sqrt(365)-btc_data.query("Date<=@end_date").iloc[-1].volatility
    btc_range = btc_data.query("Date<=@end_date and Date>=@start_date")
    return x["imply_vol"]/np.sqrt(365)-btc_range["log_ret"].std()

price_result["vol_pre"] = price_result.apply(get_vol_pre, axis=1)

price_result["amihud"]=btc_data["amihud"].loc[pd.DatetimeIndex(price_result["date"]).date].values

# money_cut_more=pd.cut(price_result["S/X"],[0, 0.6, 0.9,1.1,1.4,2.0,3.9],right=True)
# mean_isd=price_result.groupby(money_cut_more)["imply_vol"].mean()
# mean_isd.index=pd.Series(mean_isd.index).apply(lambda x:(x.left+x.right)/2).astype("double")
# z=price_result.dropna(subset={"imply_vol"})
# mean_isd[price_result["S/X"].min()-0.0001]=z["imply_vol"].loc[z["S/X"].idxmin()]
# mean_isd[price_result["S/X"].max()]=z["imply_vol"].loc[z["S/X"].idxmax()]
# mean_isd=mean_isd.sort_index()

# mean_isd.plot()
# plt.savefig("drift/figures/isd_plot.png")

money_cut_more=pd.cut(price_result["S/X"],[0.3,0.6, 0.9,1.1,1.4,2.0,3.9],right=True)
mean_isd=price_result.groupby(money_cut_more)["imply_vol"].mean()
mean_isd.index=pd.Series(mean_isd.index).apply(lambda x:(x.left+x.right)/2).astype("double")

mean_isd[price_result["S/X"].max()]=price_result["imply_vol"].loc[price_result["S/X"].idxmax()]
mean_isd=mean_isd.sort_index()
plt.plot(mean_isd)
plt.savefig("drift/figures/mean_isd.png")
def get_slope(x):
    moneyness=x["S/X"]
    locate=mean_isd.index.searchsorted(moneyness)
    if locate>0:
        return (mean_isd.iloc[locate]-mean_isd.iloc[locate-1])/(mean_isd.index[locate]-mean_isd.index[locate-1])

    else:
        print("error!")
        return float("nan")
price_result["slope"]=price_result.apply(get_slope,axis=1)
price_result["spread"] = price_result["last_ask"]-price_result["last_bid"]
exchanges_price_data = pd.read_excel("data/bitcoinity_data.xlsx")
exchanges_price_data["max"] = exchanges_price_data.max(axis=1)
exchanges_price_data["min"] = exchanges_price_data.min(axis=1)
exchanges_price_data.index = exchanges_price_data["Time"]
exchanges_price_data.index = exchanges_price_data.index.date
btc_data["maxmin_ratio"] = exchanges_price_data["max"].loc[btc_data.index.date] / \
    exchanges_price_data["min"].loc[btc_data.index.date]
price_result["maxmin_ratio"] = btc_data["maxmin_ratio"].loc[pd.DatetimeIndex(
    price_result["date"]).date].values


price_result.rename(columns={"Volume":"btc_volume"},inplace=True)
used_data = price_result[["bias","delta_5", "S/X","time", "vol_pre", "log_ret", "volatility", "skewness", "kurtosis","amihud",
                           "open_interest", "contract_is_call",  "maxmin_ratio","slope","btc_volume","volume"]]
used_data = used_data.dropna()
used_data = used_data.loc[-np.isinf(used_data.amihud)]
used_data["time"]=np.log(used_data["time"])
used_data["btc_volume"]=np.log(used_data["btc_volume"])
used_data["inter_call_money"]=used_data["contract_is_call"]*used_data["S/X"]
used_data["inter_put_money"]=(~used_data["contract_is_call"].astype("bool")).astype("int")*used_data["S/X"]
used_data["inter_call_skewness"]=used_data["contract_is_call"]*used_data["skewness"]
used_data.rename(columns={"delta_5":"delta"},inplace=True)
used_data.to_excel("new_data/data_for_regression.xlsx",index=False)
used_data=used_data[
    ["bias",
        "log_ret",
        "volatility",
        "skewness",
        "kurtosis",
        "amihud",
        "maxmin_ratio",
        "btc_volume",
        "time",
        "delta",
        "vol_pre",
        
        "open_interest",
 
        "volume",
        "contract_is_call",
        "inter_call_money",
        "inter_put_money",
        "inter_call_skewness"
    ]
]

X=used_data[
    [
        
        "log_ret",
        "volatility",
        "skewness",
        "kurtosis",
        "amihud",
        "maxmin_ratio",
        "btc_volume",
        "time",
        "delta",
        "vol_pre",
        
        "open_interest",

        "volume",
        "contract_is_call",
        "inter_call_money",
        "inter_put_money",
        "inter_call_skewness"
    ]
]

X_descr=X.describe()
with open("drift/new_describes/independent_variables_describe.tex","w") as f:
    latex_str=X_descr.to_latex(float_format=lambda x: "{:.2f}".format(
        x) if not np.isnan(x) else " ")
    f.write(latex_str)
X_descr.to_excel("new_data/independent_variables_describe.xlsx",index=False)
X_corr=X.corr()
with open("drift/new_describes/independent_variables_corr.tex","w") as f:
    latex_str=X_corr.to_latex(float_format=lambda x: "{:.2f}".format(
        x) if not np.isnan(x) else " ")
    f.write(latex_str)

X_corr.to_excel("new_data/independent_variables_corr.xlsx")
used_data.to_excel("new_data/data_for_regression.xlsx",index=False)
model_1_stepwise=stf.ols('''bias ~ log_ret + kurtosis + maxmin_ratio + amihud+btc_volume+
    delta + vol_pre + open_interest + time + contract_is_call + 
    inter_call_money + inter_put_money''',data=used_data,hasconst=True).fit()
summaries = summary_col([model_1_stepwise], stars=True, model_names=["定价偏差"],info_dict={
                        "observations": lambda x: x.nobs, "R-Squared": lambda x: x.rsquared, "Adjusted R-Squared": lambda x: x.rsquared_adj})
re_for_tabular = re.compile(r"\\begin{tabular}[\d\D]*\\end{tabular}")


def cut(x):
    x = re_for_tabular.findall(x)[0]
    return x


with open("drift/new_describes/regression_table.tex", "w",encoding="utf-8") as f:
    tex = summaries.as_latex()
    tex = cut(tex)
    f.write(tex)

price_result["contract_is_call"] = price_result["contract_is_call"].astype(bool)
price_result.to_excel("new_data/filtered_price_result.xlsx",index=False)
