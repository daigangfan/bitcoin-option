
import pandas as pd
price_result = pd.read_excel("data/price_result.xlsx")
price_result_after_time=price_result.query("time>7")
price_result_after_volume=price_result_after_time.query("volume>1")
calls=price_result_after_volume.query("contract_is_call==1")
puts=price_result_after_volume.query("contract_is_call==0")
callquantile=calls["S/X"].quantile(6.7/100)
putquantile=puts["S/X"].quantile(3.3/100)
price_result_filtered=price_result_after_volume.loc[
    (price_result_after_volume.contract_is_call & (price_result_after_volume["S/X"]>callquantile)) |
    (~price_result_after_volume.contract_is_call & (price_result_after_volume["S/X"]<putquantile))
]
writer=pd.ExcelWriter("data/filtered_price_result.xlsx")
with writer:
    price_result_filtered.to_excel(writer,index=False)

