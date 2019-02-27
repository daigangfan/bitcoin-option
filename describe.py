# 用于生成描述性统计表格
import pandas as pd
import datetime
price_result=pd.read_excel("price_result.xlsx")
btc_data=pd.read_excel("btc_data.xlsx")
def get_time(x):
    start_time=x["date"]
    end_time=x["exp_date"]
    return (end_time-start_time).days
price_result["time"]=price_result.apply(get_time,axis=1)


