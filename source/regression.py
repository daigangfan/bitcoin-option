import statsmodels.api as sts 
from statsmodels.iolib.summary2 import summary_col
import pandas as pd
import numpy as np
from imply_vol import calc_imp_vol
import datetime
import re 
price_result = pd.read_excel("data/price_result.xlsx")
btc_data = pd.read_excel("data/btc_data.xlsx")

price_result = pd.merge(left=price_result, right=btc_data[[
                        "Date", "skewness", "kurtosis", "log_ret"]], left_on="date", right_on="Date", how="left")
price_result.drop(columns=["Date"], inplace=True)

price_result["imply_vol"] = price_result.apply(calc_imp_vol, axis=1)
price_result["contract_is_call"] = price_result["contract_is_call"].astype(int)

# TODO: 计算波动率溢价时对于超过11月2日数据的两种选择：①：将波动率截止到11月2日（现在存在一定问题） ②：去掉到期日在11月2日之后的数据。
# 30天以内的波动率用30天的窗口计算


def get_vol_pre(x):
    start_date = x["date"]
    end_date = x["exp_date"]
    if x["time"] < 30:
        return x["imply_vol"]/np.sqrt(365)-btc_data.query("Date<=@end_date").iloc[-1].volatility
    btc_range = btc_data.query("Date<=@end_date and Date>=@start_date")
    return x["imply_vol"]/np.sqrt(365)-btc_range["log_ret"].std()


price_result["vol_pre"] = price_result.apply(get_vol_pre,axis=1)


price_result["amihud"]=np.abs(np.log(price_result["volume"]).divide(price_result["log_ret"]))
price_result["spread"]=price_result["last_ask"]-price_result["last_bid"]

used_data=price_result[["S/X","time","vol_pre","log_ret","volatility","skewness","amihud","spread","open_interest","contract_is_call","bias_int5","abs_bias_int5"]]
used_data=used_data.dropna()
used_data = used_data.loc[-np.isinf(used_data.amihud)]

X = used_data[["S/X", "time", "vol_pre", "log_ret", "volatility", "skewness",  "amihud", "spread",
               "open_interest","contract_is_call"]]
X.loc[:,"time"]=np.log(X["time"])
X.loc[:,"inter_call_money"]=X["contract_is_call"]*X["S/X"]
X.loc[:,"inter_skewness"]=X["contract_is_call"]*X["skewness"]
X=sts.add_constant(X)
y1=used_data["bias_int5"]
y2=used_data["abs_bias_int5"]

model = sts.OLS(y1, X)
result = model.fit()

# result_robust=model.fit(cov_type="hc1")
# result_robust.summary()
model2 = sts.OLS(y2, X)
result2 = model2.fit()
result2
# result2_robust=model2.fit(cov_type="hc1")
# result2_robust.summary()
summaries=summary_col([result,result2],stars=True,info_dict={"observations":lambda x:x.nobs,"R-Squared":lambda x:x.rsquared,"Adjusted R-Squared":lambda x:x.rsquared_adj})
re_for_tabular=re.compile(r"\\begin{tabular}[\d\D]*\\end{tabular}")
def cut(x):
    x=re_for_tabular.findall(x)[0]
    return x
with open("drift/regression_table.tex","w") as f:
    tex=summaries.as_latex()
    tex=cut(tex)
    f.write(tex)

writer=pd.ExcelWriter("data/price_result.xlsx")
with writer:
    price_result.to_excel(writer,index=False)
    