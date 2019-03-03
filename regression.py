import statsmodels
import pandas as pd
import numpy as np
from imply_vol import calc_imp_vol

price_result = pd.read_excel("price_result.xlsx")
btc_data = pd.read_excel("btc_data.xlsx")

price_result = pd.merge(left=price_result, right=btc_data[[
                        "Date", "skewness", "kurtosis", "log_ret"]], left_on="date", right_on="Date", how="left")
price_result.drop(columns=["Date"], inplace=True)

# FIXME: 这里计算隐含波动率的有问题
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


price_result["vol_pre"] = price_result
