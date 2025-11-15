import pandas as pd
import yfinance as yf
import numpy as np

shareholding_pattern = pd.read_csv('fianl_df_normal_pivot.csv',index_col='report_date',parse_dates=True)

shareholding_pattern = shareholding_pattern.fillna(0)

stocks = shareholding_pattern.columns.tolist()
print(f"✅ Loaded {len(stocks)} stocks from file.")

start_date = shareholding_pattern.index.min() - pd.Timedelta(days=10)
end_date = shareholding_pattern.index.max() +  pd.Timedelta(days=30)

ticker = [s + '.NS' for s in stocks]
all_price = yf.download(ticker,start=start_date,end=end_date,auto_adjust=False)['Close']
all_price.columns = [c.replace(".NS",'') for c in all_price.columns]

print("✅ Price data fetched successfully.")

quaterly_price = all_price.reindex(shareholding_pattern.index,method='ffill')

market_caps = shareholding_pattern*quaterly_price
print(market_caps)

weights_per_quarter = {}
for date,row in market_caps.iterrows():
    row = row.replace([np.inf, -np.inf], np.nan).fillna(0)
    top20_caps = row.nlargest(20)
    total = top20_caps.sum()
    weights = top20_caps/total
    weights_per_quarter[date]=weights

# === Step 6: Build Index (Quarterly Rebalancing) ===
index_series = pd.Series(dtype=float)
index_value = 1000

for i,date in enumerate(shareholding_pattern.index):
    try:
        start = date
        end = shareholding_pattern.index[i+1] if i<len(shareholding_pattern.index)-1 else all_price.index[-1]

        weights = weights_per_quarter[date]
        active_stocks = weights.index

        sub_price = all_price.loc[start:end,active_stocks].dropna(how="all",axis=1)
        normalized = sub_price/sub_price.iloc[0]

        segment_index = (normalized*weights).sum(axis=1)
        segment_index = segment_index/segment_index.iloc[0] * index_value

        if not index_series.empty:
            segment_index = segment_index * (index_series.iloc[-1]/segment_index.iloc[0])
        index_series = pd.concat([index_series, segment_index])  
        index_value = index_series.iloc[-1]
    except Exception as e:
        print(f"⚠️ Error at {date}: {e}")    


index_series = index_series[~index_series.index.duplicated(keep="last")]

print("\n✅ Market Cap Weighted Index successfully created!")
nifty = yf.download('^NSEI',start='2018-03-1')['Close']
nifty = nifty[index_series.index[0]:]
nifty = nifty/nifty.iloc[0]*1000
import matplotlib.pyplot as plt

plt.figure(figsize=(10,5))
plt.plot(index_series, label="Custom Market-Cap Weighted Index")
plt.plot(nifty,label='Index')
plt.title("Quarterly Rebalanced Market Cap Index (Base 1000)")
plt.xlabel("Date")
plt.ylabel("Index Value")
plt.legend()
plt.show()