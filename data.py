import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
import requests
from dateutil import relativedelta

from bs4 import BeautifulSoup
import numpy as np 

date1 = datetime(2017, 10, 17)
delta = relativedelta.relativedelta(days=1)

sess = requests.Session()

# get option data from ledgerX

def fetch_data(date):
    url = "https://data.ledgerx.com/json/{}.json".format(
        date.strftime("%Y-%m-%d"), verify=False)
    content = sess.get(url)
    if content.status_code == 200:
        data = json.loads(content.content)
        report_data = data["report_data"]
        report_data = pd.DataFrame(report_data)
        report_data["date"] = date.strftime("%Y-%m-%d")
        return report_data


results = pd.DataFrame()
with ThreadPoolExecutor(20) as executor:
    to_do = []
    while date1 <= datetime(2018, 12, 31):
        future = executor.submit(fetch_data, date1
                                 )
        to_do.append(future)
        date1 = date1 + delta
    for future in as_completed(to_do):
        res = future.result()
        results = results.append(res)

results.sort_values("date", inplace=True)
results.dropna(subset=["contract_is_call"], axis=0, inplace=True)
results = results.query("volume>0")
results.iloc[0, results.columns.get_loc("contract_label")] = "BTC 2017-10-27 Put $5600.00"

m = results["contract_label"].apply(
    lambda x: pd.Series(x.split(" "), index=["cointype", "exp_date", "optiontype", "strike"]))
results = pd.concat([results, m], axis=1)

def fix_contract_label(x:str):
    x=x.replace(",","")
    return x
results["contract_label"]=results["contract_label"].apply(fix_contract_label)

def fix_strike(x: str):
    x = x.strip("$")
    x = x.replace(",", "")
    return float(x)


results["strike"] = results["strike"].apply(fix_strike)

# 修正价格
results["vwap"] = results["vwap"] / 100
results["last_ask"] = results["last_ask"] / 100
results["last_bid"] = results["last_bid"] / 100
results["date"] = results["date"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))
results["exp_date"] = results["exp_date"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))

writer = pd.ExcelWriter("ledgerx_data.xlsx")
with writer:
    results.to_excel(writer)

# get bitcoin data from coinmarketcap,move all preprocessing for btc_data here
page=sess.get("https://coinmarketcap.com/currencies/bitcoin/historical-data/?start=20170801&end=20190304")
if page.status_code==200:
    source=page.content
    soup=BeautifulSoup(source)
    table=soup.find("table",{"class":"table"})
    btc_data=pd.read_html(table.decode())[0]
    btc_data.rename(columns={"Open*":"Open","Close**":"Price"},inplace=True)


else:
    print("获取比特币数据出错")
    raise Exception("获取比特币数据出错")

btc_data["Date"] = btc_data["Date"].apply(
    lambda x: datetime.strptime(x, r"%b %d, %Y"))
btc_data.sort_values("Date", inplace=True)
btc_data["log_ret"]=pd.Series(np.log(btc_data["Price"])).diff()

writer=pd.ExcelWriter("btc_data.xlsx")
with writer:
    btc_data.to_excel(writer)