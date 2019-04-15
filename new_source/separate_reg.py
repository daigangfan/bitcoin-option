
from statsmodels.iolib.summary2 import summary_col
import pandas as pd
import numpy as np
from imply_vol import calc_imp_vol
import datetime
import re
from math import log, exp, sqrt
from scipy.stats import norm
from statsmodels.formula import api as stf
price_result = pd.read_excel("new_data/data_for_regression.xlsx")
calls=price_result.query("contract_is_call==1")
puts=price_result.query("contract_is_call==0")
calls.rename(columns={"inter_call_money":"moneyness"},inplace=True)
puts.rename(columns={"inter_put_money":"moneyness"},inplace=True)
model_call=stf.ols("bias ~ log_ret + kurtosis+amihud + maxmin_ratio + btc_volume + delta_5 + vol_pre + open_interest + slope+moneyness",data=calls,hasconst=True).fit()
model_put=stf.ols("bias ~ log_ret + kurtosis+amihud + maxmin_ratio + btc_volume + delta_5 + vol_pre + open_interest + slope+moneyness",data=puts,hasconst=True).fit()
summaries = summary_col([model_call,model_put], model_names=["认购期权偏差","认沽期权偏差"],stars=True, info_dict={
                        "observations": lambda x: x.nobs, "R-Squared": lambda x: x.rsquared, "Adjusted R-Squared": lambda x: x.rsquared_adj})
re_for_tabular = re.compile(r"\\begin{tabular}[\d\D]*\\end{tabular}")


def cut(x):
    x = re_for_tabular.findall(x)[0]
    return x


with open("drift/new_describes/seperate_regression_table.tex", "w",encoding="utf-8") as f:
    tex = summaries.as_latex()
    tex = cut(tex)
    f.write(tex)

