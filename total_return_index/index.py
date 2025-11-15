import pandas as pd
import numpy as np

base_date = pd.Timestamp('2019-01-02')
base_value = 1000

prices = pd.read_csv('price_data.csv',parse_dates=['date'],dayfirst=True,usecols=['date','ticker','close'])
prices['date'] = pd.to_datetime(prices['date'],format='%d-%m-%Y',errors='coerce')
prices.drop_duplicates(subset=['date','ticker'],inplace=True)

shares = pd.read_csv('shareholiding_pattern.csv',parse_dates=['report_date'],usecols=['promoter_shares','public_shares','total_shares','free_float_factor','ticker','report_date'])
shares['report_date'] = pd.to_datetime(shares['report_date'],format='%Y-%m-%d')
shares.rename(columns={'report_date':'date'},inplace=True)
shares.drop_duplicates(subset=['date','ticker'],keep='last',inplace=True)

divs = pd.read_csv('dividends.csv',parse_dates=['EX-DATE','RECORD DATE'],usecols=['SYMBOL','COMPANY NAME','PURPOSE','EX-DATE','RECORD DATE','payout_per_s'])
divs.rename(columns={'SYMBOL':'ticker','EX-DATE':'ex-date'},inplace=True)
divs.drop_duplicates(inplace=True)

corp = pd.read_csv('corporate_actions.csv',usecols=['SYMBOL','PURPOSE','EX-DATE','RECORD DATE','event_type','ratio'])
corp['EX-DATE'] = pd.to_datetime(corp['EX-DATE'],format='%d-%b-%y',errors='coerce')
corp['RECORD DATE'] = pd.to_datetime(corp['RECORD DATE'],format='%d-%b-%y',errors='coerce')
corp.rename(columns={'SYMBOL':'ticker','EX-DATE':'ex-date'},inplace=True)
corp.drop_duplicates(inplace=True)

all_dates = prices['date'].drop_duplicates().sort_values()

price_w = prices.pivot(index='date', columns='ticker', values='close').reindex(all_dates).ffill()
shares_w = shares.pivot(index='date', columns='ticker', values='total_shares').reindex(all_dates).ffill()
float_factors = shares.pivot(index='date', columns='ticker', values='free_float_factor').reindex(all_dates).ffill()


float_shares = shares_w * float_factors
market_cap = price_w * float_shares 
index_market_cap = market_cap.apply(lambda r: r.sort_values(ascending=False).head(20).sum(), axis=1)


index_market_cap = index_market_cap.sort_index()
idx = index_market_cap.index.get_indexer([base_date], method='nearest')[0]
nearest_base_date = index_market_cap.index[idx]


base_market_cap = index_market_cap.loc[nearest_base_date]
PRI = (index_market_cap / base_market_cap) * base_value
PRI = PRI.sort_index()

PRI.plot(kind='line')




