
import pandas as pd
from math import isnan
price_result = pd.read_excel("new_data/price_result.xlsx")
price_result_after_time=price_result.query("time>7")
price_result_after_volume=price_result_after_time.query("volume>1")
# #暂时先留下2以下的
# price_result_filtered=price_result_after_volume.query("const_bias<=2")
call_quantile=price_result_after_volume.query("contract_is_call")["S/X"].quantile(20/100)
put_quantile=price_result_after_volume.query("not contract_is_call")["S/X"].quantile(1-10/100)
price_result_filtered=price_result_after_volume.loc[
    (price_result_after_volume.contract_is_call & (price_result_after_volume["S/X"]>0.8)) |
    (~price_result_after_volume.contract_is_call & (price_result_after_volume["S/X"]<1.25))
]

filtered_out=price_result_after_volume.loc[
    (price_result_after_volume.contract_is_call & (price_result_after_volume["S/X"]<=0.8)) |
    (~price_result_after_volume.contract_is_call & (price_result_after_volume["S/X"]>=1.25))
]
filtered_out.to_excel("new_data/filtered_out.xlsx",index=False)

price_result=price_result_filtered
price_result["time_cut"] = pd.cut(
    price_result["time"], [0, 30, 60, 180, 624], right=False)
price_result["moneyness_cut"] = pd.cut(
    price_result["S/X"], [0, 0.6, 0.9, 1.1, 3.9], right=False)

def reformat_index(x: pd.DataFrame):
    x.index = [str(a) for a in x.index]
    x.index.name = "moneyness_cut"
    x.columns = [str(a) for a in x.columns]
    x.columns.name = "time_cut"
def get_bias_groups(price_result:pd.DataFrame,name=""):
    price_result_grouped = price_result.groupby(["time_cut", "moneyness_cut"])
    const_bias_mean=price_result_grouped["bias"].mean()

    const_bias_mean = const_bias_mean.unstack("time_cut")

    block_counts = price_result_grouped.size()
    block_counts = block_counts.unstack("time_cut")
    reformat_index(const_bias_mean)
    reformat_index(block_counts)

    time_cut_mean = price_result.groupby("time_cut")["bias"].mean()
    moneyness_cut_mean = price_result.groupby("moneyness_cut")["bias"].mean()

    time_cut_mean.index = [str(a) for a in time_cut_mean.index]
    moneyness_cut_mean.index = [str(a) for a in moneyness_cut_mean.index]

    const_bias_mean.loc["mean"] = time_cut_mean
    const_bias_mean["mean"] = moneyness_cut_mean
    with open("drift/new_describes/{}_option_bias_group.tex".format(name), "w") as f:
        latex_str = const_bias_mean.to_latex(float_format=lambda x: "{:.3f}".format(
            x) if not isnan(x) else " ")
        latex_str = latex_str.replace("[", "")
        latex_str = latex_str.replace(")", "")

        f.write(latex_str)

    with open("drift/new_describes/{}_option_counts_group.tex".format(name),"w") as f:
        latex_str = block_counts.to_latex(float_format=lambda x: "{:.0f}".format(
            x) if not isnan(x) else " ")
        latex_str = latex_str.replace("[", "")
        latex_str = latex_str.replace(")", "")

        f.write(latex_str)
get_bias_groups(price_result)
get_bias_groups(price_result.query("contract_is_call"),name="call")
get_bias_groups(price_result.query("not contract_is_call"),name="put")

writer=pd.ExcelWriter("new_data/filtered_price_result.xlsx")
with writer:
    price_result.to_excel(writer,index=False)
result_describe=price_result["bias"].describe()
result_describe.name="定价偏差"

call_describe=price_result.query("contract_is_call")["bias"].describe()
call_describe.name="认购期权定价偏差"


put_describe=price_result.query("not contract_is_call")["bias"].describe()
put_describe.name="认沽期权定价偏差"

total_describe=pd.concat([result_describe,call_describe,put_describe],axis=1)
with open("drift/new_describes/dependent_variables_describe.tex","w",encoding="utf-8") as f:
    latex_str=total_describe.to_latex(float_format=lambda x: "{:.3f}".format(
        x) if not isnan(x) else " ")
    f.write(latex_str)
