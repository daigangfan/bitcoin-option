import requests
from datetime import datetime
from dateutil import relativedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import pandas as md
import json
import pandas as pd

date1 = datetime(2017, 10, 17)
delta = relativedelta.relativedelta(days=1)

sess = requests.Session()
def fetch_data(date):
    url = "https://data.ledgerx.com/json/{}.json".format(
        date.strftime("%Y-%m-%d"),verify=False)
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
        date1 = date1+delta
    for future in as_completed(to_do):
        res = future.result()
        results = results.append(res)

results.sort_values("date",inplace=True)
results.dropna(subset=["contract_is_call"],axis=0,inplace=True)
results.iloc[0,results.columns.get_loc("contract_label")]="BTC 2017-10-27 Call $5600.00"
results.iloc[1,results.columns.get_loc("contract_label")]="BTC 2017-10-27 Put $5600.00"
m=results["contract_label"].apply(lambda x:pd.Series(x.split(" "),index=["cointype","exp_date","optiontype","strike"]))
results=pd.concat([results,m],axis=1)
def fix_strike(x:str):
    x=x.strip("$")
    x=x.replace(",","")
    return float(x)
results["strike"]=results["strike"].apply(fix_strike)
results=results.query("volume>0")

writer=pd.ExcelWriter("ledgerx_data.xlsx")
with writer:
    results.to_excel(writer)


