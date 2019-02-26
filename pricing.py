import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from math import log, sqrt, exp
from scipy.stats import norm

option_data = pd.read_excel("ledgerx_data.xlsx")
btc_data = pd.read_csv("BTC_USD Bitfinex Historical Data.csv")
btc_data["Date"] = btc_data["Date"].apply(
    lambda x: datetime.strptime(x, r"%b %d, %Y"))
btc_data.sort_values("Date", inplace=True)
btc_data["log_ret"] = btc_data["Change %"].apply(
    lambda x: log(1+float(x.strip('%'))/100))
delta = relativedelta(days=-30)


def get_volatility(x):
    end_date = datetime.strptime(x, r"%Y-%m-%d")
    start_date = end_date+delta
    # which side is equal?
    data_used = btc_data.query("Date<@end_date and Date>=@start_date")
    volatility = data_used["log_ret"].std()
    return volatility


def get_spot_price(x):
    date = datetime.strptime(x, "%Y-%m-%d")
    data_used = btc_data.query("Date==@date")
    return float(data_used["Price"].values[0].replace(",", ""))


option_data["volatility"] = option_data["date"].apply(get_volatility)
option_data["spot_price"] = option_data["date"].apply(get_spot_price)
def Pricing(x,ints=0.05):
    maturity_date=datetime.strptime(x["exp_date"],"%Y-%m-%d")
    start_date=datetime.strptime(x["date"],"%Y-%m-%d")
    time=((maturity_date-start_date).days+1)/365
    if time>0:
        
        spot_price=x["spot_price"]
        strike_price=x["strike"]
        volatility=x["volatility"]*sqrt(365)
        d1=(log(spot_price/strike_price)+ints*time)/(volatility*sqrt(time))+0.5*(volatility*sqrt(time))
        d2=(log(spot_price/strike_price)+ints*time)/(volatility*sqrt(time))-0.5*(volatility*sqrt(time))
        if x["optiontype"].lower()=="call":
            price=spot_price*norm.cdf(d1)-strike_price*exp(-ints*time)*norm.cdf(d2)
        if x["optiontype"].lower()=="put":
            price=strike_price*exp(-ints*time)*norm.cdf(-d2)-spot_price*norm.cdf(-d1)
        return price
    else:
        return float("nan")
prices=pd.DataFrame()
prices["int5"]=option_data.apply(Pricing,axis=1,ints=0.05)
prices["int10"]=option_data.apply(Pricing,axis=1,ints=0.1)
prices["int20"]=option_data.apply(Pricing,axis=1,ints=0.2)
prices["int30"]=option_data.apply(Pricing,axis=1,ints=0.3)
price_result=pd.concat([option_data,prices],axis=1)
