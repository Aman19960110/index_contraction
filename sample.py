"""
index_builder_quarterly.py
----------------------------------------
Builds a custom market-cap-weighted index of multiple stocks
with quarterly rebalancing, using yfinance data.

Author: Aman
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# ============================================================
# =============== USER CONFIGURATION =========================
# ============================================================

STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS",
    "KOTAKBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "AXISBANK.NS", "NTPC.NS", "POWERGRID.NS", "TITAN.NS", "ULTRACEMCO.NS"
]

START_DATE = "2024-01-01"
BASE_VALUE = 1000
REBAL_FREQ = "QE"     # Quarterly end (use 'QE' instead of 'Q')

# ============================================================
# =============== HELPER FUNCTIONS ===========================
# ============================================================

def get_latest_market_caps(stocks):
    """Fetch latest market caps using yfinance."""
    caps = {}
    for s in stocks:
        try:
            info = yf.Ticker(s).info
            caps[s] = info.get("marketCap", np.nan)
        except Exception as e:
            print(f"⚠️ Could not fetch market cap for {s}: {e}")
            caps[s] = np.nan
    return pd.Series(caps).dropna()


def get_nearest_trading_date(df, date):
    """Return nearest trading day from df.index to given date."""
    return df.index[df.index.get_indexer([date], method='nearest')[0]]


def build_quarterly_index(data, base_value=1000):
    """
    Build market-cap weighted index with quarterly rebalancing.
    """
    # Rebalance dates (end of each quarter)
    rebal_dates = data.resample(REBAL_FREQ).last().index
    index_values = pd.Series(index=data.index, dtype=float)

    divisor = None
    prev_index = None

    for i, rebal_date in enumerate(rebal_dates):
        # Determine start and end of the quarter
        if i == 0:
            start = data.index[0]
        else:
            start = rebal_dates[i - 1]
        end = rebal_date

        # Align start and end to nearest trading days
        start = get_nearest_trading_date(data, start)
        end = get_nearest_trading_date(data, end)

        # Get base prices
        prices_start = data.loc[start]

        # Fetch latest market caps for all stocks
        market_caps = get_latest_market_caps(data.columns)
        market_caps = market_caps.reindex(data.columns).ffill()

        # Compute number of shares for this quarter
        shares = market_caps / prices_start

        # Calculate the raw index values for the quarter
        quarter_data = data.loc[start:end]
        quarter_index_raw = (quarter_data * shares).sum(axis=1)

        # Set or adjust divisor
        if divisor is None:
            divisor = quarter_index_raw.iloc[0] / base_value
        else:
            divisor = quarter_index_raw.iloc[0] / prev_index.iloc[-1]

        # Calculate normalized index for this quarter
        quarter_index = quarter_index_raw / divisor
        index_values.loc[start:end] = quarter_index

        prev_index = quarter_index

        print(f"✅ Rebalanced on {end.date()} | Divisor: {divisor:.4f}")

    return index_values.ffill()


# ============================================================
# ===================== MAIN SCRIPT ==========================
# ============================================================

if __name__ == "__main__":
    print("📊 Downloading stock data...")
    data = yf.download(STOCKS, start=START_DATE, auto_adjust=True)["Close"]
    data = data.dropna(how="all")

    print("⚙️ Building quarterly rebalanced index...")
    custom_index = build_quarterly_index(data, base_value=BASE_VALUE)
    print("\n✅ Index construction complete!\n")
    print(custom_index.tail())

    # Plot the result
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 5))
    plt.plot(custom_index, label="Custom Market Cap Weighted Index", lw=2)
    plt.title("Custom Market Cap Weighted Index (Quarterly Rebalanced)")
    plt.xlabel("Date")
    plt.ylabel("Index Level")
    plt.legend()
    plt.grid(True)
    plt.show()
