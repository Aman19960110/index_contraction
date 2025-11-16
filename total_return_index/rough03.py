import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


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



# -----------------------------
# 2. BUILD TRADING CALENDAR
# -----------------------------
all_dates = pd.date_range(
    start=prices.date.min(), 
    end=prices.date.max(), 
    freq='B'
)

price_w = prices.pivot(index="date", columns="ticker", values="close").reindex(all_dates).ffill()

# -----------------------------
# 2. BUILD CLEAN SHARES TIMELINE (no incorrect ffill across long gaps)
# -----------------------------
# Important dates are those when shares data exists and corporate events (where shares could change)
dates_from_shares = set(shares["date"].dropna().unique())
dates_from_corp = set(corp["ex_date"].dropna().unique())
dates_from_divs = set(divs["ex_date"].dropna().unique())    # sometimes ex_date matters
dates_from_prices = set(price_w.index)                     # keep price dates to allow alignment later

important_dates = sorted(dates_from_shares.union(dates_from_corp).union(dates_from_divs).union(dates_from_prices))

# Pivot shares on important dates only (so we only ffill between real known checkpoints)
shares_imp = shares.pivot(index="date", columns="ticker", values="shares_outstanding").reindex(important_dates).sort_index()

# Forward fill known values, then backward-fill earlier missing values (so earliest known snapshot is used backwards)
shares_imp = shares_imp.ffill().bfill()

# Similarly free-float factors; if missing, assume 1 (or bfill/ffill depending on your preference)
floatfac_imp = shares.pivot(index="date", columns="ticker", values="free_float_factor").reindex(important_dates).sort_index()
floatfac_imp = floatfac_imp.ffill().bfill().fillna(1.0)

# Now expand the cleaned step-function series to full daily calendar safely
shares_w = shares_imp.reindex(all_dates).ffill()
floatfac_w = floatfac_imp.reindex(all_dates).ffill().fillna(1.0)

# -----------------------------
# 3. APPLY SPLITS / BONUS / CORPORATE ACTIONS
# -----------------------------
# We assume corp['ratio'] is either "old:new" (e.g., "1:5") or numeric factor.
# For SPLIT / BONUS: new_shares = old_shares * (new/old); price divides by same factor on ex-date onward.
# We apply changes on ex_date: multiply shares from ex_date onward, divide prices from ex_date onward.

# Make a copy so we can mutate
price_adj = price_w.copy()
shares_adj = shares_w.copy()

for _, row in corp.dropna(subset=["event_type"]).iterrows():
    t = str(row["ticker"])
    ex = row["ex_date"]
    event = str(row["event_type"]).upper()
    ratio = row.get("ratio", None)

    if pd.isna(ex) or t not in price_adj.columns:
        continue

    # compute factor
    try:
        if isinstance(ratio, str) and ":" in ratio:
            old_s, new_s = ratio.split(":")
            factor = float(new_s) / float(old_s)
        elif ratio is None or (isinstance(ratio, float) and np.isnan(ratio)):
            # if no ratio given, skip (or set factor=1)
            factor = 1.0
        else:
            factor = float(ratio)
    except Exception:
        factor = 1.0

    # align ex date to calendar (use nearest prior trading day if necessary)
    if ex not in shares_adj.index:
        # get index position to ffill/backfill
        pos = shares_adj.index.get_indexer([ex], method="ffill")
        if pos.size and pos[0] >= 0:
            ex_idx = shares_adj.index[pos[0]]
        else:
            ex_idx = shares_adj.index[0]
    else:
        ex_idx = ex

    if event in ["SPLIT", "BONUS"]:
        # apply from ex_idx onwards
        shares_adj.loc[ex_idx:, t] = shares_adj.loc[ex_idx:, t] * factor
        # prevent division by zero
        price_adj.loc[ex_idx:, t] = price_adj.loc[ex_idx:, t] / factor

# Replace any remaining NaNs in shares/prices with zeros (safer for mcap math)
shares_adj = shares_adj.fillna(0.0)
price_adj = price_adj.fillna(method="ffill").fillna(0.0)

# -----------------------------
# 4. COMPUTE FLOAT SHARES & MARKET CAPS
# -----------------------------
float_shares = shares_adj * floatfac_w
mcap = price_adj * float_shares   # DataFrame: dates x tickers
index_mcap = mcap.sum(axis=1)     # Series

# -----------------------------
# 5. BASE DATE / BASE VALUES
# -----------------------------
base_date = index_mcap.index[0]   # first trading day in price data
base_value = 1000.0
base_mcap = index_mcap.loc[base_date]
if base_mcap == 0:
    raise ValueError("Base market cap is zero at base_date, check input data.")

# -----------------------------
# 6. PROCESS DIVIDENDS (normal vs special)
# -----------------------------
# We'll compute:
# - indexed_div_cash[date] = sum of normal dividend cash paid to index on ex-date (absolute cash)
# - For special dividends, we'll remove cash from mcap on ex-date (so PRI is adjusted)
indexed_div_cash = pd.Series(0.0, index=mcap.index)

# Helper: price lookup for announcement date (fallback to price_adj on ex_date)
price_lookup = prices.set_index(["date", "ticker"])["close"]

for _, row in divs.iterrows():
    t = str(row["ticker"])
    payout = row.get("payout_per_share", np.nan)
    ex = row.get("ex_date", pd.NaT)
    ann_date = row.get("announcement_date", pd.NaT)
    short_flag = bool(row.get("short_notice_flag", False))

    if pd.isna(ex) or t not in float_shares.columns or pd.isna(payout):
        continue

    # find announcement price if possible
    ann_price = None
    try:
        if not pd.isna(ann_date):
            ann_price = price_lookup.loc[(ann_date, t)]
    except Exception:
        ann_price = None

    if ann_price is None or pd.isna(ann_price):
        # fallback to price on ex date
        if ex in price_adj.index:
            ann_price = price_adj.loc[ex, t]
        else:
            # nearest prior available price
            pos = price_adj.index.get_indexer([ex], method="ffill")
            if pos.size and pos[0] >= 0:
                ann_price = price_adj.iat[pos[0], price_adj.columns.get_loc(t)]
            else:
                ann_price = 0.0

    # determine special dividend
    percent = (payout / ann_price) if (ann_price and ann_price > 0) else 0.0
    is_special = (percent >= 0.02) or short_flag

    # align ex date to calendar
    if ex not in float_shares.index:
        pos = float_shares.index.get_indexer([ex], method="ffill")
        ex_idx = float_shares.index[pos[0]] if (pos.size and pos[0] >= 0) else float_shares.index[0]
    else:
        ex_idx = ex

    float_sh = float_shares.loc[ex_idx, t]
    if pd.isna(float_sh) or float_sh == 0:
        continue

    if is_special:
        # remove cash from mcap on ex-date (adjust PRI)
        cash_removed = payout * float_sh
        # Subtract from the ticker's mcap on ex-date (and hence from index mcap)
        mcap.loc[ex_idx, t] = max(0.0, mcap.loc[ex_idx, t] - cash_removed)
        # Recompute index_mcap for that date
        index_mcap.loc[ex_idx] = mcap.loc[ex_idx].sum()
    else:
        # normal dividend -> add to indexed_div_cash (absolute cash)
        total_div = payout * float_sh
        indexed_div_cash.loc[ex_idx] += total_div

# After specials changed some mcap on certain ex-dates, we should propagate index_mcap forward for subsequent dates:
# Recompute index_mcap as sum of mcap (in case we edited some ticker mcap above)
index_mcap = mcap.sum(axis=1)
base_mcap = index_mcap.loc[base_date]   # recompute/in case changed
if base_mcap == 0:
    raise ValueError("Base market cap is zero after special dividend adjustments. Check data.")

# -----------------------------
# 7. PREPARE FOR QUARTERLY TOP-20 REBALANCE
# -----------------------------
# Quarter end dates (use last trading day of each calendar quarter from price_adj)
rebal_dates = price_adj.resample("Q").last().index
rebal_dates = [d for d in rebal_dates if d >= price_adj.index[0] and d <= price_adj.index[-1]]

# index_units DataFrame that will hold the number of shares (units) the index holds of each ticker
index_units = pd.DataFrame(0.0, index=price_adj.index, columns=price_adj.columns)

# We'll iterate chronological rebal_dates, set index units on each rebalance and carry forward
prev_units = None

for idx, rdate in enumerate(rebal_dates):
    # align rdate to calendar index if needed
    if rdate not in price_adj.index:
        rdate = price_adj.index[price_adj.index.get_indexer([rdate], method="ffill")[0]]

    # Compute market caps on rebal date
    mcaps_today = mcap.loc[rdate].copy().fillna(0.0)
    # select tickers with positive market cap
    mcaps_today = mcaps_today[mcaps_today > 0]

    if len(mcaps_today) == 0:
        # nothing to do
        continue

    # select top 20 by market cap
    top20 = mcaps_today.sort_values(ascending=False).head(20)
    top20_tickers = top20.index.tolist()

    # weights (market-cap weighted)
    weights = top20 / top20.sum()

    # compute current portfolio value BEFORE rebalancing:
    # if this is the first rebalance (base), set portfolio_val = base_value
    if idx == 0:
        portfolio_val = base_value
    else:
        # portfolio value from prev_units and today's prices at rdate
        # prev_units should have been carried forward in index_units already
        portfolio_val = (index_units.loc[rdate] * price_adj.loc[rdate]).sum()

        # If portfolio_val is zero (maybe prev had no units), fall back to base_value
        if portfolio_val == 0 or pd.isna(portfolio_val):
            portfolio_val = base_value

    # Units to hold for each top20 ticker on rdate
    units = (weights * portfolio_val) / price_adj.loc[rdate, top20_tickers]

    # set units at rdate
    index_units.loc[rdate, top20_tickers] = units

    # carry forward these units until next rebalance (or until end)
    if idx < len(rebal_dates) - 1:
        next_date = rebal_dates[idx + 1]
        # align next_date to index
        if next_date not in price_adj.index:
            next_date = price_adj.index[price_adj.index.get_indexer([next_date], method="ffill")[0]]
        index_units.loc[rdate:next_date, :] = index_units.loc[rdate, :].values
    else:
        # last rebal: carry to end
        index_units.loc[rdate:, :] = index_units.loc[rdate, :].values

# For any dates before the first rebal, carry the first units backward (if desired)
first_rebal = rebal_dates[0] if len(rebal_dates) > 0 else price_adj.index[0]
if first_rebal in index_units.index:
    index_units.loc[:first_rebal] = index_units.loc[first_rebal].values

# -----------------------------
# 8. DAILY PORTFOLIO VALUE -> PRI_portfolio
# -----------------------------
portfolio_value = (index_units * price_adj).sum(axis=1)   # daily portfolio mark-to-market

# If portfolio_value at base_date is zero (edge case), set to base_value scale using index_mcap
if portfolio_value.loc[base_date] == 0:
    # fallback: scale index by market cap
    PRI = (index_mcap / base_mcap) * base_value
else:
    PRI = (portfolio_value / portfolio_value.loc[base_date]) * base_value

# -----------------------------
# 9. COMPUTE TRI USING INDEXED DIVIDENDS
# -----------------------------
# Convert absolute indexed_div_cash (cash) to index points consistent with PRI units:
# indexed_div_points = (indexed_div_cash / base_mcap) * base_value
indexed_div_points = (indexed_div_cash / base_mcap) * base_value

# Ensure alignment
indexed_div_points = indexed_div_points.reindex(PRI.index).fillna(0.0)

# multiplier = (PRI_t + indexed_div_points_t) / PRI_{t-1}
PRI_prev = PRI.shift(1)
mult = (PRI + indexed_div_points) / PRI_prev
mult.iloc[0] = 1.0  # first day no change

TRI = base_value * mult.cumprod()

# -----------------------------
# 10. SAVE RESULTS
# -----------------------------
result = pd.DataFrame({
    "Index_MarketCap": index_mcap,
    "Portfolio_Value": portfolio_value,
    "PRI": PRI,
    "Indexed_Dividend_Points": indexed_div_points,
    "TRI": TRI
})

result.to_csv("TRI_top20_quarterly_rebalanced.csv", index=True)
print("Saved TRI_top20_quarterly_rebalanced.csv")

# Optionally save index_units and top-20 timeline for debugging/inspection
index_units.to_csv("index_units_top20.csv")
print("Saved index_units_top20.csv")