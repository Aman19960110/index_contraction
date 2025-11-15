import yfinance as yf
import pandas as pd
nifty50_since_2018 = [
    "ADANIENT", "ADANIPORTS", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO",
    "BAJAJFINSV", "BAJFINANCE", "BAJAJHLDNG", "BHARTIARTL", "BPCL",
    "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
    "EICHERMOT", "GAIL", "GRASIM", "HCLTECH", "HDFCBANK",
    "HDFCLIFE", "HINDALCO", "HINDUNILVR", "ICICIBANK", "ICICIGI",
    "ICICIPRULI", "INDIGO", "INDUSINDBK", "INFY", "IOC",
    "ITC", "JSWSTEEL", "JIOFINANCIL", "KOTAKBANK", "LT",
    "LTIM", "M&M", "MARUTI", "MAXHEALTH", "NESTLEIND",
    "NTPC", "ONGC", "RELIANCE", "SBILIFE", "SBIN",
    "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SUNPHARMA", "TATACONSUM",
    "TATAMOTORS", "TATAPOWER", "TATASTEEL", "TCS", "TECHM",
    "TITAN", "ULTRACEMCO", "UPL", "VEDL", "WIPRO", "YESBANK",
    "AMBUJACEM", "HINDPETRO", "IBULHSGFIN", "VEDL", "ZEEL",
    "BEL", "APOLLOHOSP"
]
failed_list =[]
collected_data = []


for s in nifty50_since_2018:
    df = yf.download(f'{s}.NS', start='2018-01-01', auto_adjust=False, multi_level_index=False)[['Close']]
    df = df.reset_index()
    df['ticker'] = s
    df = df.rename(columns={'Close': 'close', 'Date': 'date'})
    collected_data.append(df[['date', 'ticker', 'close']])

# Concatenate vertically to create the final long-format DataFrame
data = pd.concat(collected_data, ignore_index=True)

print(data.head())


data = pd.concat(collected_data,axis=0)
data.head()
data.to_csv('price_data.csv')


df = pd.read_csv('price_data.csv',parse_dates=True,usecols=['date','ticker','close'])

df[df.duplicated(subset=['date','ticker','close'])]

df.drop_duplicates(keep="first",inplace=True)

np.where((df['ticker']=='ADANIENT'))

df.pivot(index='date',columns='ticker',values='close')

# collecting data for shares



