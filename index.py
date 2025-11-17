import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

NO_STOCKS = 20
BASE_INDEX_VALUE = 1000.0
REBALANCE_FREQ = "QE"

#flags
make_csv = False

price = pd.read_csv('price_data.csv',parse_dates=['date'])
price.drop_duplicates(subset=['date','ticker'],inplace=True)
price_w = price.pivot(index='date',columns='ticker',values='close')
rebal_dates = price_w.resample(REBALANCE_FREQ).last().index

shareholding_pattern_w = pd.read_csv('outstanding_shares.csv',parse_dates=['date'],index_col='date')


quaterly_price = price_w.reindex(rebal_dates,method='ffill')

market_caps = shareholding_pattern_w*quaterly_price

weights_per_quater ={}
for date,row in market_caps.iterrows():
    top20_caps = row.nlargest(NO_STOCKS)
    total = top20_caps.sum()
    weights = top20_caps/total
    weights_per_quater[date]=weights
if make_csv:
    weights_per_quater_csv = pd.DataFrame(weights_per_quater)
    weights_per_quater_csv.to_csv(f'weights_per_quater_{NO_STOCKS}.csv')
index_series = pd.Series(dtype=float)
index_value = 1000

for i,date in enumerate(rebal_dates):
    try:
        start = date
        end = rebal_dates[i+1] if i<len(rebal_dates)-1 else price_w.index[-1]

        weights = weights_per_quater[date]
        active_stocks = weights.index

        sub_price = price_w.loc[start:end,active_stocks].dropna(how='all',axis=1)
        normalized = sub_price/sub_price.iloc[0]

        segment_index = (normalized*weights).sum(axis=1)
        segment_index = segment_index/segment_index.iloc[0] * index_value

        if not index_series.empty:
            segment_index = segment_index * (index_series.iloc[-1]/segment_index.iloc[0])
        index_series = pd.concat([index_series, segment_index])
        index_value = index_series.iloc[-1]

    except Exception as e:
        print(f'Error at {date}: {e}')


index_series = index_series[~index_series.index.duplicated(keep="last")]
if make_csv:
    index_series.to_csv(f'index_series_{NO_STOCKS}.csv')
"""print("\n✅ Market Cap Weighted Index successfully created!")
nifty = yf.download('^NSEI',start='2018-03-1')['Close']
nifty = nifty[index_series.index[0]:]
nifty = nifty/nifty.iloc[0]*1000"""
import matplotlib.pyplot as plt

plt.figure(figsize=(10,5))
plt.plot(index_series, label="Custom Market-Cap Weighted Index")
plt.title("Quarterly Rebalanced Market Cap Index (Base 1000)")
plt.xlabel("Date")
plt.ylabel("Index Value")
plt.legend()
plt.show()