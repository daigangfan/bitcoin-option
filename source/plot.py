import matplotlib.pyplot as plt
import pandas as pd 

btc_data=pd.read_excel("data/btc_data.xlsx")
plt.style.use("classic")
btc_data.index=btc_data["Date"]
btc_data["maxmin_ratio"].plot()
plt.savefig("drift/figures/maxmin_ratio_plot.png")