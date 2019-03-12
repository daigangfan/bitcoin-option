from imply_vol import calc_imp_vol
import pandas as pd 

price_result=pd.read_excel("data/price_result.xlsx")
missing=price_result[(price_result["is_inbound"])&(price_result["imply_vol"].isna())]

