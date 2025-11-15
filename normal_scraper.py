from xbrl_parese_02 import parse_xbrl_shareholding, extract_summary_values
import pandas as pd
from logger_config import setup_logger
import glob

logger = setup_logger('logs','log_files')


files = glob.glob('links/*.csv')
logger.debug(f'total files {len(files)}')
logger.debug(f'{files[:5]}')




collected_data = []
failed_url = []
for _,file in enumerate(files):  
    logger.info(f'file name - {file}')
    symbol = file.split('-')[4]
    logger.info(f'symbol is {symbol}')
    excel = pd.read_csv(file)
    logger.debug(f'excel df.head {excel.head()}')
    urls = excel['ACTION']
    logger.debug(f'total urls - {urls.shape}')
    for _,url in enumerate(urls):
        try:
            logger.info(f'fetching data for url {url}')
            data = parse_xbrl_shareholding(url)
            report_date = data['ReportDate'].iloc[0]
            summary = extract_summary_values(data)
            summary['ticker'] = symbol
            summary['report_date'] = report_date
            collected_data.append(summary)
            logger.info(f'adding dict to list - {summary}')
        except Exception as e:
            logger.debug(f'failed to extract this url {url}')
            failed_url.append(url)
logger.info('all data collected')

final_df = pd.DataFrame(collected_data)
final_df.to_csv('shareholiding_pattern.csv')