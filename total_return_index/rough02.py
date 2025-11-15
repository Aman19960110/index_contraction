import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -------------------------------
# 1. Base settings
# -------------------------------
base_value = 1000
base_date = pd.Timestamp('2019-01-01')


# -------------------------------
# 2. PRICE DATA
# -------------------------------
prices = pd.read_csv(
    'price_data.csv',
    parse_dates=['date'],
    dayfirst=True,
    usecols=['date', 'ticker', 'close']
).drop_duplicates()

# Ensure datetime & sort dates
prices['date'] = pd.to_datetime(prices['date'], errors='coerce')
prices = prices.dropna(subset=['date'])

all_dates = prices['date'].drop_duplicates().sort_values()  # ensures datetime index


# -------------------------------
# 3. SHAREHOLDING PATTERN DATA
# -------------------------------
shares = pd.read_csv(
    'shareholiding_pattern.csv',
    parse_dates=['report_date'],
    usecols=[
        'promoter_shares', 'public_shares', 'total_shares',
        'free_float_factor', 'ticker', 'report_date'
    ]
)

shares.rename(columns={'report_date': 'date'}, inplace=True)

# Ensure datetime
shares['date'] = pd.to_datetime(shares['date'], errors='coerce')
shares = shares.dropna(subset=['date'])

# drop duplicates (VERY IMPORTANT)
shares.drop_duplicates(subset=['date', 'ticker'], keep='last', inplace=True)


# -------------------------------
# 4. DIVIDENDS DATA
# -------------------------------
divs = pd.read_csv(
    'dividends.csv',
    parse_dates=['EX-DATE', 'RECORD DATE'],
    dayfirst=True,
    usecols=['SYMBOL', 'COMPANY NAME', 'PURPOSE', 'EX-DATE', 'RECORD DATE', 'payout_per_s']
)

divs.rename(columns={'SYMBOL': 'ticker', 'EX-DATE': 'ex_date'}, inplace=True)
divs.drop_duplicates(inplace=True)


# -------------------------------
# 5. CORPORATE ACTIONS (Split, Bonus)
# -------------------------------
corp = pd.read_csv(
    'corporate_actions.csv',
    usecols=[
        'SYMBOL', 'PURPOSE', 'EX-DATE', 'RECORD DATE',
        'event_type', 'old_face_value', 'new_face_value', 'ratio'
    ]
)

corp.rename(columns={'SYMBOL': 'ticker', 'EX-DATE': 'ex_date'}, inplace=True)

# Parse NSE date format DD-MMM-YY
corp['ex_date'] = pd.to_datetime(corp['ex_date'], format='%d-%b-%y', errors='coerce')
corp['RECORD DATE'] = pd.to_datetime(corp['RECORD DATE'], format='%d-%b-%y', errors='coerce')
corp.drop_duplicates(inplace=True)


# -------------------------------
# 6. BUILD WIDE MATRICES (price, shares, float factor)
# -------------------------------
price_w = (
    prices.pivot(index='date', columns='ticker', values='close')
          .reindex(all_dates)
          .ffill()
)

shares_w = (
    shares.pivot(index='date', columns='ticker', values='total_shares')
          .reindex(all_dates)
          .ffill()
)

float_factors = (
    shares.pivot(index='date', columns='ticker', values='free_float_factor')
          .reindex(all_dates)
          .ffill()
)

# Float-adjusted shares
float_shares = shares_w * float_factors


# -------------------------------
# 7. MARKET CAP CALCULATION
# -------------------------------
market_cap = price_w * float_shares

# Top 20 stocks per day
index_market_cap = market_cap.apply(
    lambda row: row.nlargest(20).sum(),
    axis=1
)

# IMPORTANT: convert index to datetime
index_market_cap.index = pd.to_datetime(index_market_cap.index, errors='coerce')
index_market_cap = index_market_cap.dropna()


# -------------------------------
# 8. PRICE RETURN INDEX (PRI)
# -------------------------------
# Safely select nearest valid trading day
idx = index_market_cap.index.get_indexer([base_date], method='nearest')[0]
nearest_base_date = index_market_cap.index[idx]

base_mc = index_market_cap.loc[nearest_base_date]

PRI = (index_market_cap / base_mc) * base_value
PRI = PRI.sort_index()

# Plot
plt.figure(figsize=(12, 6))
PRI.plot(kind='line', title='Price Return Index (Top 20 Market Cap)')
plt.xlabel("Date")
plt.ylabel("Index Level")
plt.grid(True)
plt.show()

print("PRI constructed successfully!")
