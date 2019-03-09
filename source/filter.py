
import pandas as pd
price_result = pd.read_excel("data/price_result.xlsx")
price_result_after_time=price_result.query("time>7")
price_result_after_volume=price_result.query("volume>1")

