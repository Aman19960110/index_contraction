import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

nifty50_2018 = ["ADANIPORTS", "AMBUJACEM", "ASIANPAINT", "AUROPHARMA", "AXISBANK",
                "BAJAJ-AUTO", "BAJFINANCE", "BPCL", "BHARTIARTL", "INFRATEL",
                "BOSCHLTD", "CIPLA", "COALINDIA", "DRREDDY", "EICHERMOT",
                "GAIL", "HCLTECH", "HDFCBANK", "HEROMOTOCO", "HINDALCO",
                "HINDUNILVR", "HDFC", "ITC", "ICICIBANK", "IBULHSGFIN",
                "IOC", "INDUSINDBK", "INFY", "KOTAKBANK", "LT",
                "LUPIN", "M&M", "MARUTI", "NTPC", "ONGC",
                "POWERGRID", "RELIANCE", "SBIN", "SUNPHARMA", "TCS",
                "TATAMOTORS", "TATASTEEL", "TECHM", "UPL", "ULTRACEMCO",
                "VEDL", "WIPRO", "YESBANK", "ZEEL"]

START_DATE = "2018-01-01"
BASE_VALUE = 1000
REBAL_FREQ = "QE"

def get_nearest_trading_date(df, date):
    """Return nearest trading day from df.index to given date."""
    return df.index[df.index.get_indexer([date], method='nearest')[0]]

def get_nearest_sharesholding_date(start,end,df,date):
    df = df.loc[start:end]
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
        shares_df = pd.read_csv('fianl_df_normal_pivot.csv',parse_dates=['report_date'],index_col='report_date')
        nearest_shareholding_date = get_nearest_sharesholding_date(start,end,shares_df,start)

        shares = shares_df.loc[nearest_shareholding_date]
   

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

    data = yf.download([s + '.NS' for s in nifty50_2018], start=START_DATE, auto_adjust=True)["Close"]
    data = data.dropna(how="all")

    print("⚙️ Building quarterly rebalanced index...")
    custom_index = build_quarterly_index(data, base_value=BASE_VALUE)
    print("\n✅ Index construction complete!\n")
    print(custom_index.tail())