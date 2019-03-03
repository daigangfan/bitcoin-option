from scipy.stats import norm 
from scipy.optimize import fsolve
from math import *
def bs_price(v,target,optiontype,S,K,T,r):
    d1=(log(S/K)+r*T)/(v*sqrt(T))+0.5*v*sqrt(T)
    d2=(log(S/K)+r*T)/(v*sqrt(T))-0.5*v*sqrt(T)
    if optiontype=="Call":
        p=S*norm.cdf(d1)-K*exp(-r*T)*norm.cdf(d2)
    else:
        p=K*exp(-r*T)*norm.cdf(-d2)-S*norm.cdf(-d1)
    return p-target

def Root(target,optiontype,S,K,T,r,v):
    init_sigma=v*sqrt(365)
    root=fsolve(bs_price,x0=init_sigma,args=(target,optiontype,S,K,T,r),full_output=True)
    if root[2]==1:
        return root[0][0]
    else:
        return float("nan")

def calc_imp_vol(x,r=0.05):
    
    imp_vol=Root(x["vwap"],x["optiontype"],x["spot_price"],x["strike"],x["time"]/365,r,x["volatility"])
    return imp_vol

