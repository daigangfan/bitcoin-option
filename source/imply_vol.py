from scipy.stats import norm
from scipy.optimize import brentq
from math import *


def bs_price(v, target, optiontype, S, K, T, r):
    d1 = (log(S/K)+r*T)/(v*sqrt(T))+0.5*v*sqrt(T)
    d2 = (log(S/K)+r*T)/(v*sqrt(T))-0.5*v*sqrt(T)
    if optiontype == "Call":
        p = S*norm.cdf(d1)-K*exp(-r*T)*norm.cdf(d2)
    else:
        p = K*exp(-r*T)*norm.cdf(-d2)-S*norm.cdf(-d1)
    return p-target


def Root(target, optiontype, S, K, T, r, v):
    try:
        root = brentq(bs_price, 1e-3, 100, args=(target, optiontype,
                                                 S, K, T, r), maxiter=1000, full_output=True)
    except Exception:
        return float("nan")
    if root[1].converged:
        return root[0]
    else:
        return float("nan")


def calc_imp_vol(x, r=0.05):

    imp_vol = Root(x["vwap"], x["optiontype"], x["spot_price"],
                   x["strike"], x["time"]/365, r, x["volatility"])
    return imp_vol
