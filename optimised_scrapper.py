import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import glob
from xbrl_parse import parse_xbrl_shareholding
from logger_config import setup_logger

logger = setup_logger("ShareholdingLogger")

# --- Load all URLs efficiently ---
files = glob.glob('links/*.csv')
logger.info(f"Found {len(files)} CSV files")

# Merge all CSVs
dfs = [pd.read_csv(f) for f in files]
all_urls = pd.concat(dfs, ignore_index=True)
logger.info(f"Total URLs to process: {len(all_urls)}")
all_urls = all_urls[~(all_urls['ACTION'].str.contains('/null'))]
# --- Prepare containers ---
collected_data = []
failed_url = []

# --- Define processing function ---
def process_url(row):
    url = row['ACTION']
    symbol = row.get('COMPANY', 'UNKNOWN')
    try:
        data = parse_xbrl_shareholding(url)
        data = data[data['category'] == 'ShareholdingPattern'][['ReportDate','NumberOfShares']]
        row_data = data.iloc[0]
        result = {
            'symbol': symbol,
            'report_date': row_data['ReportDate'],
            'total_shares': row_data['NumberOfShares']
        }
        return result
    except Exception as e:
        logger.debug(f"Failed: {url} | {e}")
        return None

# --- Run concurrent threads ---
MAX_WORKERS = 10  # adjust based on system + network
logger.info(f"Starting parallel fetch with {MAX_WORKERS} threads...")

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(process_url, row) for _, row in all_urls.iterrows()]

    for i, future in enumerate(as_completed(futures), 1):
        result = future.result()
        if result:
            collected_data.append(result)
        else:
            failed_url.append(i)
        if i % 10 == 0:
            logger.info(f"Processed {i}/{len(futures)} URLs")

logger.info("✅ All data fetched.")

# --- Save results ---
final_df = pd.DataFrame(collected_data)
final_df.to_csv('final_df.csv', index=False)
logger.info(f"Saved {len(final_df)} rows to final_df.csv")
