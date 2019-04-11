import statsmodels.api as sts
from statsmodels.iolib.summary2 import summary_col
import pandas as pd
import numpy as np
from imply_vol import calc_imp_vol
import datetime
import re
from math import log, exp, sqrt
from scipy.stats import norm
from statsmodels.formula import api as stf
price_result = pd.read_excel("data/price_result.xlsx")
btc_data = pd.read_excel("data/btc_data.xlsx")
used_data = price_result[["delta_5", "time", "vol_pre", "log_ret", "volatility", "skewness", "amihud",
                          "spread", "open_interest", "contract_is_call", "bias_int5", "abs_bias_int5", "maxmin_ratio","slope"]]
used_data = used_data.dropna()
used_data = used_data.loc[-np.isinf(used_data.amihud)]
desc=used_data.describe()
with open("drift/independent_variables_describe.tex","w") as f:
    latex_str=desc.to_latex(float_format=lambda x: "{:.2f}".format(
        x) if not isnan(x) else " ")
    f.write(latex_str)
