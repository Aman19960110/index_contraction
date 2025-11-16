import pandas as pd


price = pd.read_csv('price_data.csv',parse_dates=['date'])
price.drop_duplicates(subset=['date','ticker'],inplace=True)
price_w = price.pivot(index='date',columns='ticker',values='close')


REBALANCE_FREQ = "QE"
rebal_dates = price_w.resample(REBALANCE_FREQ).last().index
df = pd.read_csv('shareholiding_pattern.csv',parse_dates=['report_date'])[['report_date','ticker','total_shares']]
df.drop_duplicates(subset=['report_date','ticker'],inplace=True)
df_p = df.pivot(index='report_date',columns='ticker',values='total_shares').ffill().reindex(rebal_dates,method='ffill')

df_p.isna().sum()

df_p['MAXHEALTH'].fillna(0,inplace=True)

df_p.iloc[0] = df_p.iloc[0].fillna(df_p.iloc[1])


df_p.to_csv('outstanding_shares.csv')