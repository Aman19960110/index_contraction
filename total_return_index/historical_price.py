import yfinance as yf
import pandas as pd
nifty50_union = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS",
    "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "BEL.NS", "BHARTIARTL.NS", "CIPLA.NS", "COALINDIA.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "ETERNAL.NS", "GRASIM.NS",
    "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS", "HINDALCO.NS",
    "HINDUNILVR.NS", "ICICIBANK.NS", "INDIGO.NS", "INFY.NS",
    "ITC.NS", "JIOFIN.NS", "JSWSTEEL.NS", "KOTAKBANK.NS",
    "LT.NS", "M&M.NS", "MARUTI.NS", "MAXHEALTH.NS",
    "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS",
    "RELIANCE.NS", "SBILIFE.NS", "SHRIRAMFIN.NS", "SBIN.NS",
    "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS", "TMPV.NS",
    "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "TRENT.NS",
    "ULTRACEMCO.NS", "WIPRO.NS",

    # Removed but were part of NIFTY 50 since 2018
    "AMBUJACEM.NS", "AUROPHARMA.NS", "BOSCHLTD.NS", "LUPIN.NS",
    "HINDPETRO.NS", "YESBANK.NS", "VEDL.NS",
    "ZEEL.NS", "INFRATEL.NS", "DIVISLAB.NS", "GAIL.NS",
    "IOC.NS", "SHREECEM.NS", "UPL.NS",
    "LTIM.NS", "BPCL.NS", "BRITANNIA.NS", "HEROMOTOCO.NS",
    "INDUSINDBK.NS"
]

failed_list =[]
collected_data = []


for s in nifty50_since_2018:
    try:
        df = yf.download(f'{s}.NS', start='2018-01-01', auto_adjust=True, multi_level_index=False)[['Close']]
        df = df.reset_index()
        df['ticker'] = s
        df = df.rename(columns={'Close': 'close', 'Date': 'date'})
        collected_data.append(df[['date', 'ticker', 'close']])
    except Exception as e:
        print(e)
# Concatenate vertically to create the final long-format DataFrame
#data = pd.concat(collected_data, )




data = pd.concat(collected_data,axis=0,ignore_index=True)
data.head()
data.to_csv('price_data_02.csv')


df = pd.read_csv('price_data.csv',parse_dates=True,usecols=['date','ticker','close'])

df[df.duplicated(subset=['date','ticker','close'])]

df.drop_duplicates(keep="first",inplace=True)

np.where((df['ticker']=='ADANIENT'))

df.pivot(index='date',columns='ticker',values='close')

# collecting data for shares



