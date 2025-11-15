import pandas as pd
df = pd.read_csv('fianl_df_normal.csv',usecols=[1,2,3])
df = df.drop_duplicates(subset=['report_date','symbol'],keep='first')
df_pivot = df.pivot(
    index='report_date',
    columns='symbol',
    values='total_shares'
).reset_index()

df_pivot = df_pivot.ffill()
df_pivot.to_csv('fianl_df_normal_pivot.csv',index=False)



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


df_weights = pd.DataFrame(weights_per_quarter)

df_weights.pivot(
    index= 
)

df_weights.to_csv('weights.csv')

df=pd.read_json('https://iislliveblob.niftyindices.com/jsonfiles/HeatmapDetail/FinalHeatmapNIFTY%2050.json')
