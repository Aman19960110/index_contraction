import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

NO_STOCKS = 20
BASE_INDEX_VALUE = 1000.0     # initial investment
REBALANCE_FREQ = "QE"

# flags
make_csv = False

# -----------------------------
# 1) Load & prepare price data
# -----------------------------
price = pd.read_csv('price_data.csv', parse_dates=['date'])
price.drop_duplicates(subset=['date', 'ticker'], inplace=True)
price_w = price.pivot(index='date', columns='ticker', values='close')

# Rebalance dates from price data
rebal_dates = price_w.resample(REBALANCE_FREQ).last().index

# -----------------------------
# 2) Load outstanding shares
# -----------------------------
shareholding_pattern_w = pd.read_csv(
    'outstanding_shares.csv',
    parse_dates=['date'],
    index_col='date'
)

# Align shareholding to quarter ends
shareholding_q = shareholding_pattern_w.reindex(rebal_dates).ffill()

# -----------------------------
# 3) Quarterly prices
# -----------------------------
quaterly_price = price_w.reindex(rebal_dates, method='ffill')

# -----------------------------
# 4) Market caps & weights
# -----------------------------
market_caps = shareholding_q * quaterly_price

weights_per_quarter = {}

for date, row in market_caps.iterrows():
    top20 = row.nlargest(NO_STOCKS)
    weights = top20 / top20.sum()
    weights_per_quarter[date] = weights

if make_csv:
    pd.DataFrame(weights_per_quarter).to_csv(f'weights_per_quarter_{NO_STOCKS}.csv')

# -----------------------------
# 5) Dynamic index + shares
# -----------------------------
index_series = pd.Series(dtype=float)
portfolio_value = BASE_INDEX_VALUE

shares_held_per_quarter = {}

for i, date in enumerate(rebal_dates):
    try:
        print(f"Processing quarter: {date.date()}")

        # Find next rebalance or final date
        start = date
        end = rebal_dates[i+1] if i < len(rebal_dates)-1 else price_w.index[-1]

        # Weight selection
        weights = weights_per_quarter[date]
        active_stocks = weights.index

        # -----------------------------
        # (A) Compute number of shares at this rebalance
        # -----------------------------
        prices_at_rebalance = quaterly_price.loc[date, active_stocks]
        money_alloc = weights * portfolio_value
        shares = money_alloc / prices_at_rebalance

        # Save shares for reporting
        shares_held_per_quarter[date] = shares

        # -----------------------------
        # (B) Compute index movement inside this quarter
        # -----------------------------
        sub_price = price_w.loc[start:end, active_stocks].dropna(how='all', axis=1)
        normalized = sub_price / sub_price.iloc[0]

        segment_index = (normalized * weights).sum(axis=1)
        segment_index = segment_index / segment_index.iloc[0] * portfolio_value

        # Smooth stitching to previous period
        if not index_series.empty:
            scale_factor = index_series.iloc[-1] / segment_index.iloc[0]
            segment_index = segment_index * scale_factor

        index_series = pd.concat([index_series, segment_index])

        # -----------------------------
        # (C) Update portfolio for next quarter
        # -----------------------------
        portfolio_value = index_series.iloc[-1]

    except Exception as e:
        print(f"Error at {date}: {e}")

# ---------------------------------
# 6) Cleanup duplicate dates
# ---------------------------------
index_series = index_series[~index_series.index.duplicated(keep="last")]

if make_csv:
    index_series.to_csv(f'index_series_{NO_STOCKS}.csv')
    pd.DataFrame(shares_held_per_quarter).to_csv("shares_held_dynamic.csv")

# ---------------------------------
# 7) Plot final index
# ---------------------------------
plt.figure(figsize=(10,5))
plt.plot(index_series, label="Custom Quarterly Market-Cap Index")
plt.title("Dynamic Portfolio Index (Top 20, Quarterly Rebalancing)")
plt.xlabel("Date")
plt.ylabel("Index Value")
plt.legend()
plt.show()
