from scipy.stats import norm 
from math import *
def bs_price(optiontype,S,K,T,r,v):
    d1=(log(S/K)+r*T)/(v*sqrt(T))+0.5*v*sqrt(T)
    d2=(log(S/K)+r*T)/(v*sqrt(T))-0.5*v*sqrt(T)
    if optiontype=="Call":
        p=S*norm.cdf(d1)-K*exp(-r*T)*norm.cdf(d2)
    else:
        p=K*exp(-r*T)*norm.cdf(-d2)-S*norm.cdf(-d1)
    return p

def bs_vega(optiontype,S,K,T,r,v):
    d1=(log(S/K)+r*T)/(v*sqrt(T))+0.5*v*sqrt(T)
    return S*sqrt(T)*norm.pdf(d1)

def Newton(target,optiontype,S,K,T,r,v,niter=1000,tol=1e-3):
    init_sigma=sqrt(365)*sqrt(2*pi/T)*target/S
    sigma=init_sigma
    for x in range(niter):
        price=bs_price(optiontype,S,K,T,r,sigma)
        vega=bs_vega(optiontype,S,K,T,r,sigma)
        
        diff=target-price
        #print("{0}round: {1}target, {2}price,{3}diff,{4}vega".format(x,target,price,diff,vega))
        if (abs(diff)<tol):
            return sigma 
        sigma=sigma+diff/vega
    return float("nan")

def calc_imp_vol(x,r=0.05,niter=1000,tol=1e-4):
    
    imp_vol=Newton(x["vwap"],x["optiontype"],x["spot_price"],x["strike"],x["time"]/365,r,x["volatility"],niter=niter,tol=tol)
    return imp_vol

