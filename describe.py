# 用于生成描述性统计表格
import pandas as pd
import datetime
price_result=pd.read_excel("price_result.xlsx")
btc_data=pd.read_csv("BTC_USD Bitfinex Historical Data.csv")
def get_time(x):
    start_time=x["date"]