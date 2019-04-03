import pandas as pd 
import numpy as np 
import datetime
import statsmodels.formula.api as smf
price_result=pd.read_excel("data/price_result.xlsx")
btc_data=pd.read_excel("data/btc_data.xlsx")
btc_data.index=btc_data["Date"]
def get_realized_return(x):
    start_date=x["date"]
    end_date=x["exp_date"]
    used_data=btc_data[start_date:end_date]
    realized_return=np.log(used_data.iloc[-1]["Price"]/used_data.iloc[0]["Price"])
    return realized_return/x["time"]

def get_next_return(x):
    start_date=x["date"]
    next_return=btc_data.loc[start_date+datetime.timedelta(days=1)]["log_ret"]
    return next_return
price_result["realized_return"]=price_result.apply(get_realized_return,axis=1)
print(price_result[["realized_return","imply_vol"]].corr())
price_result["next_return"]=price_result.apply(get_next_return,axis=1)
print(price_result[["next_return","imply_vol"]].corr())
model=smf.ols(formula="next_return~imply_vol",data=price_result,hasconst=True).fit()

# result between weighted ISD and log return next term
z=btc_data[["log_ret","weighted_ISD"]]
z["weighted_ISD"]=z["weighted_ISD"].shift(1)
smf.ols(formula="log_ret~weighted_ISD",data=z,hasconst=True).fit().summary()
# result between volatility and log return next term
z1=btc_data[["log_ret","volatility"]]
z1["volatility"]=z1["volatility"].shift(1)
smf.ols(formula="log_ret~volatility",data=z,hasconst=True).fit().summary()

# result between price and weighted ISD next term
z=btc_data[["Price","weighted_ISD"]]
z["weighted_ISD"]=z["weighted_ISD"].shift(-1)
smf.ols(formula="weighted_ISD~Price",data=z,hasconst=True).fit().summary()

# result between price and volatility next term
z1=btc_data[["Price","volatility"]]
z1["volatility"]=z1["volatility"].shift(-1)
smf.ols(formula="volatility~Price",data=z1,hasconst=True).fit().summary()