
from statsmodels.iolib.summary2 import summary_col
import pandas as pd
import numpy as np
from imply_vol import calc_imp_vol
import datetime
import re
from math import log, exp, sqrt
from scipy.stats import norm
from statsmodels.formula import api as stf
filtered_price_result = pd.read_excel("data/filtered_price_result.xlsx")
btc_data = pd.read_excel("data/btc_data.xlsx")
if "skewness" not in filtered_price_result.columns:
    filtered_price_result = pd.merge(left=filtered_price_result, right=btc_data[[
        "Date", "skewness", "kurtosis", "log_ret","Volume"]], left_on="date", right_on="Date", how="left")
    filtered_price_result.drop(columns=["Date"], inplace=True)

filtered_price_result["imply_vol"] = filtered_price_result.apply(calc_imp_vol, axis=1)
filtered_price_result["contract_is_call"] = filtered_price_result["contract_is_call"].astype(int)


def get_implied_vega(x, ints=0.05):
    spot_price = x["spot_price"]
    strike_price = x["strike"]
    time = x["time"]/365
    volatility = x["imply_vol"]
    d1 = (log(spot_price/strike_price)+ints*time) /\
        (volatility*sqrt(time))+0.5*(volatility*sqrt(time))
    result = spot_price*norm.pdf(d1)*sqrt(time)
    return result


filtered_price_result["imply_vega"] = filtered_price_result.apply(get_implied_vega, axis=1)


def get_weighted_ISD(x: pd.DataFrame):
    elasticity = x["imply_vega"]*x["imply_vol"]/x["vwap"]
    return (x["imply_vol"]*elasticity).sum()/elasticity.sum()

daily_weighted_ISD = filtered_price_result.groupby("date").apply(get_weighted_ISD)
btc_data.index = btc_data["Date"]
btc_data["weighted_ISD"] = daily_weighted_ISD

# get volatility premium

def get_vol_pre(x):
    start_date = x["date"]
    end_date = x["exp_date"]
    if x["time"] < 30:
        return x["imply_vol"]/np.sqrt(365)-btc_data.query("Date<=@end_date").iloc[-1].volatility
    btc_range = btc_data.query("Date<=@end_date and Date>=@start_date")
    return x["imply_vol"]/np.sqrt(365)-btc_range["log_ret"].std()


filtered_price_result["vol_pre"] = filtered_price_result.apply(get_vol_pre, axis=1)

filtered_price_result["amihud"]=btc_data["amihud"].loc[pd.DatetimeIndex(filtered_price_result["date"]).date].values

# get the slope in the volatility curve

money_cut_more=pd.cut(filtered_price_result["S/X"],[0, 0.3,0.6, 0.9,1.1,1.4,2.0,3.9],right=True)
mean_isd=filtered_price_result.groupby(money_cut_more)["imply_vol"].mean()
mean_isd.index=pd.Series(mean_isd.index).apply(lambda x:(x.left+x.right)/2).astype("double")
mean_isd[filtered_price_result["S/X"].min()-0.0001]=filtered_price_result["imply_vol"].loc[filtered_price_result["S/X"].idxmin()]
mean_isd[filtered_price_result["S/X"].max()]=filtered_price_result["imply_vol"].loc[filtered_price_result["S/X"].idxmax()]
mean_isd=mean_isd.sort_index()

def get_slope(x):
    moneyness=x["S/X"]
    locate=mean_isd.index.searchsorted(moneyness)
    if locate>0:
        return (mean_isd.iloc[locate]-mean_isd.iloc[locate-1])/(mean_isd.index[locate]-mean_isd.index[locate-1])

    else:
        print("error!")
        return float("nan")

filtered_price_result["slope"]=filtered_price_result.apply(get_slope,axis=1)
filtered_price_result["spread"] = filtered_price_result["last_ask"]-filtered_price_result["last_bid"]
# get highest across exchanges
exchanges_price_data = pd.read_excel("data/bitcoinity_data.xlsx")
exchanges_price_data["max"] = exchanges_price_data.max(axis=1)
exchanges_price_data["min"] = exchanges_price_data.min(axis=1)
exchanges_price_data.index = exchanges_price_data["Time"]
exchanges_price_data.index = exchanges_price_data.index.date
btc_data["maxmin_ratio"] = exchanges_price_data["max"].loc[btc_data.index.date] / \
    exchanges_price_data["min"].loc[btc_data.index.date]
filtered_price_result["maxmin_ratio"] = btc_data["maxmin_ratio"].loc[pd.DatetimeIndex(
    filtered_price_result["date"]).date].values

filtered_price_result["relative_bias_int5"]=filtered_price_result["bias_int5"]/filtered_price_result["vwap"]
filtered_price_result["relative_abs_bias_int5"]=filtered_price_result["abs_bias_int5"]/filtered_price_result["vwap"]

filtered_price_result.rename(columns={"Volume":"btc_volume"},inplace=True)
filtered_price_result["bias"]=filtered_price_result["vwap"]/filtered_price_result["int5"]
used_data = filtered_price_result[["bias","delta_5", "S/X","time", "vol_pre", "log_ret", "volatility", "skewness", "amihud",
                          "spread", "open_interest", "contract_is_call", "bias_int5", "abs_bias_int5", "maxmin_ratio","slope","btc_volume","volume","relative_bias_int5","relative_abs_bias_int5"]]
used_data = used_data.dropna()
used_data = used_data.loc[-np.isinf(used_data.amihud)]
used_data["time"]=np.log(used_data["time"])
used_data["btc_volume"]=np.log(used_data["btc_volume"])
used_data["inter_call_money"]=used_data["contract_is_call"]*used_data["S/X"]
used_data["inter_put_money"]=(~used_data["contract_is_call"].astype("bool")).astype("int")*used_data["S/X"]
used_data["inter_call_skewness"]=used_data["contract_is_call"]*used_data["skewness"]

used_data=used_data[
    ["bias",
        "bias_int5",
        "abs_bias_int5",
        "relative_bias_int5",
        "relative_abs_bias_int5",
        "log_ret",
        "volatility",
        "skewness",
        "amihud",
        "maxmin_ratio",
        "btc_volume",
        "time",
        "delta_5",
        "vol_pre",
        "spread",
        "open_interest",
        "slope",
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
        "amihud",
        "maxmin_ratio",
        "btc_volume",
        "time",
        "delta_5",
        "vol_pre",
        "spread",
        "open_interest",
        "slope",
        "volume",
        "contract_is_call",
        "inter_call_money",
        "inter_put_money",
        "inter_call_skewness"
    ]
]

X_descr=X.describe()
with open("drift/independent_variables_describe.tex","w") as f:
    latex_str=X_descr.to_latex(float_format=lambda x: "{:.2f}".format(
        x) if not np.isnan(x) else " ")
    f.write(latex_str)
X_descr.to_excel("data/independent_variables_describe.xlsx")
X_corr=X.corr()
with open("drift/independent_variables_corr.tex","w") as f:
    latex_str=X_corr.to_latex(float_format=lambda x: "{:.2f}".format(
        x) if not np.isnan(x) else " ")
    f.write(latex_str)

X_corr.to_excel("data/independent_variables_corr.xlsx")

#剔除volatility、delta_5、btc_volume回归
model_1=stf.ols("bias_int5~log_ret+volatility+skewness+amihud+maxmin_ratio+time+vol_pre+spread+open_interest+slope+volume+contract_is_call+inter_call_money+inter_put_money+inter_call_skewness",data=used_data,hasconst=True).fit()

model_1_abs=stf.ols("abs_bias_int5~log_ret+volatility+skewness+amihud+maxmin_ratio+time+vol_pre+spread+open_interest+slope+volume+contract_is_call+inter_call_money+inter_put_money+inter_call_skewness",data=used_data,hasconst=True).fit()

model_2=stf.ols("relative_bias_int5~log_ret+volatility+skewness+amihud+maxmin_ratio+time+vol_pre+spread+open_interest+slope+volume+contract_is_call+inter_call_money+inter_put_money+inter_call_skewness",data=used_data,hasconst=True).fit()
model_2_abs=stf.ols("relative_abs_bias_int5~log_ret+volatility+skewness+amihud+maxmin_ratio+time+vol_pre+spread+open_interest+slope+volume+contract_is_call+inter_call_money+inter_put_money+inter_call_skewness",data=used_data,hasconst=True).fit()
summaries = summary_col([model_1,model_1_abs,model_2,model_2_abs], stars=True, info_dict={
                        "observations": lambda x: x.nobs, "R-Squared": lambda x: x.rsquared, "Adjusted R-Squared": lambda x: x.rsquared_adj})
re_for_tabular = re.compile(r"\\begin{tabular}[\d\D]*\\end{tabular}")


def cut(x):
    x = re_for_tabular.findall(x)[0]
    return x


with open("drift/regression_table.tex", "w") as f:
    tex = summaries.as_latex()
    tex = cut(tex)
    f.write(tex)


writer = pd.ExcelWriter("data/filtered_price_result.xlsx")
with writer:
    filtered_price_result.to_excel(writer, index=False)

writer = pd.ExcelWriter("data/btc_data.xlsx")
with writer:
    btc_data.to_excel(writer, index=False)



used_data.to_excel("data/data_for_regression.xlsx")

model_1_stepwise=stf.ols('''bias_int5 ~ log_ret + volatility + skewness + maxmin_ratio + 
    btc_volume + time + delta_5 + vol_pre + slope + contract_is_call + 
    inter_call_money + inter_put_money + inter_call_skewness''',data=used_data,hasconst=True).fit()

model_1_abs_stepwise=stf.ols('''abs_bias_int5 ~ log_ret + volatility + skewness + maxmin_ratio + 
    btc_volume + time + delta_5 + vol_pre + slope + contract_is_call + 
    inter_call_money + inter_put_money + inter_call_skewness''',data=used_data,hasconst=True).fit()

model_2_stepwise=stf.ols('''relative_bias_int5 ~ log_ret + volatility + skewness + maxmin_ratio + 
    btc_volume + time + delta_5 + vol_pre + slope + contract_is_call + 
    inter_call_money + inter_put_money + inter_call_skewness''',data=used_data,hasconst=True).fit()
model_2_abs_stepwise=stf.ols('''relative_abs_bias_int5 ~ log_ret + volatility + skewness + maxmin_ratio + 
    btc_volume + time + delta_5 + vol_pre + slope + contract_is_call + 
    inter_call_money + inter_put_money + inter_call_skewness''',data=used_data,hasconst=True).fit()
summaries_stepwise = summary_col([model_1_stepwise,model_1_abs_stepwise,model_2_stepwise,model_2_abs_stepwise], stars=True, info_dict={
                        "observations": lambda x: x.nobs, "R-Squared": lambda x: x.rsquared, "Adjusted R-Squared": lambda x: x.rsquared_adj})


with open("drift/regression_table_stepwise.tex", "w") as f:
    tex = summaries_stepwise.as_latex()
    tex = cut(tex)
    f.write(tex)

model_log_bias=stf.ols('''bias ~ log_ret + volatility + skewness + maxmin_ratio + 
    btc_volume + time + delta_5 + vol_pre + slope + contract_is_call + 
    inter_call_money + inter_put_money + inter_call_skewness''',data=used_data,hasconst=True).fit()
summaries_stepwise = summary_col([model_log_bias], stars=True, info_dict={
                        "observations": lambda x: x.nobs, "R-Squared": lambda x: x.rsquared, "Adjusted R-Squared": lambda x: x.rsquared_adj})
with open("drift/regression_table_bias.tex", "w") as f:
    tex = summaries_stepwise.as_latex()
    tex = cut(tex)
    f.write(tex)


from sklearn.preprocessing import StandardScaler
scaler=StandardScaler()
used_data[[
        "log_ret",
        "volatility",
        "skewness",
        "amihud",
        "maxmin_ratio",
        "btc_volume",
        "time",
        "delta_5",
        "vol_pre",
        "spread",
        "open_interest",
        "slope",
        "volume"
]]=scaler.fit_transform(used_data[[
        "log_ret",
        "volatility",
        "skewness",
        "amihud",
        "maxmin_ratio",
        "btc_volume",
        "time",
        "delta_5",
        "vol_pre",
        "spread",
        "open_interest",
        "slope",
        "volume"
]])
# describe of y:
Y=used_data[[
    "bias",
        "bias_int5",
        "abs_bias_int5",
        "relative_bias_int5",
        "relative_abs_bias_int5"
]]
Y.describe().to_excel("data/dependent_variable_describe.xlsx")