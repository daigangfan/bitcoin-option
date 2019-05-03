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
in_money=price_result.query("inter_call_money>=1 or 0<inter_put_money<=1")
out_money=price_result.query("0<inter_call_money<1 or inter_put_money>1")
long=price_result.query("time>@log(30)")
short=price_result.query("time<=@log(30)")
in_model=stf.ols('''bias ~ log_ret + kurtosis + amihud + maxmin_ratio + btc_volume + 
    delta + vol_pre + open_interest +time+ contract_is_call + 
    inter_call_money + inter_put_money''',data=in_money,hasconst=True).fit()
out_model=stf.ols('''bias ~ log_ret + kurtosis + amihud + maxmin_ratio + btc_volume + 
    delta + vol_pre + open_interest +time+ contract_is_call + 
    inter_call_money + inter_put_money''',data=out_money,hasconst=True).fit()
long_model=stf.ols('''bias ~ log_ret + kurtosis + amihud + maxmin_ratio + btc_volume + 
    delta + vol_pre + open_interest +time+ contract_is_call + 
    inter_call_money + inter_put_money''',data=long,hasconst=True).fit()
short_model=stf.ols('''bias ~ log_ret + kurtosis + amihud + maxmin_ratio + btc_volume + 
    delta + vol_pre + open_interest +time+ contract_is_call + 
    inter_call_money + inter_put_money''',data=short,hasconst=True).fit()

summaries = summary_col([in_model,out_model,long_model,short_model], model_names=["价内期权","价外期权","30天以上","30天以下"],stars=True, info_dict={
                        "observations": lambda x: x.nobs, "R-Squared": lambda x: x.rsquared, "Adjusted R-Squared": lambda x: x.rsquared_adj})
re_for_tabular = re.compile(r"\\begin{tabular}[\d\D]*\\end{tabular}")

def cut(x):
    x = re_for_tabular.findall(x)[0]
    return x


with open("drift/new_describes/subsample_regression_table.tex", "w",encoding="utf-8") as f:
    tex = summaries.as_latex()
    tex = cut(tex)
    f.write(tex)

