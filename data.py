import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
import requests
from dateutil import relativedelta

date1 = datetime(2017, 10, 17)
delta = relativedelta.relativedelta(days=1)

sess = requests.Session()


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
    while date1 <= datetime(2018, 11, 2):
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
