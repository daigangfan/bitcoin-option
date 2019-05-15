import pandas as pd 
import numpy as np
from scipy import stats
price_result = pd.read_excel("new_data/filtered_price_result.xlsx")
btc_data=pd.read_excel("new_data/btc_data.xlsx")
if "skewness" not in price_result.columns:
    price_result = pd.merge(left=price_result, right=btc_data[[
        "Date", "skewness", "kurtosis", "log_ret","Volume"]], left_on="date", right_on="Date", how="left")
    price_result.drop(columns=["Date"], inplace=True)
price_result["price_cut"]=pd.qcut(price_result["spot_price"],q=[0,0.2,0.4,0.6,0.8,1])
call_result=price_result.loc[price_result["contract_is_call"]]
call_bias_mean=call_result.groupby(call_result["price_cut"])["bias"].mean()
put_result=price_result.loc[~price_result["contract_is_call"]]
put_bias_mean=put_result.groupby(put_result["price_cut"])["bias"].mean()
results=pd.concat([call_bias_mean,put_bias_mean,put_bias_mean-call_bias_mean],axis=1)
results.columns=["认购期权平均偏差","认沽期权平均偏差","认沽-认购"]
a1=[]
for i in range(5):
    bias_call=call_result.groupby(call_result["price_cut"]).get_group(results.index[i])["bias"]
    bias_put=put_result.groupby(put_result["price_cut"]).get_group(results.index[i])["bias"]
    a1.append(stats.ttest_ind(bias_put,bias_call,equal_var=False).statistic)
results["t值"]=a1
results.index=["收益率组1","收益率组2","收益率组3","收益率组4","收益率组5"]
results=results.transpose()
with open("drift/new_describes/return_grouped_bias.tex", "w",encoding="utf-8") as f:
    f.write(results.to_latex(
        float_format=lambda x: "{:.3f}".format(x) if not np.isnan(x) else " "))