from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def download_corporate_actions_csv(ticker, download_folder=r"C:\Users\YourUserName\Downloads"):
    """
    Automates NSE Corporate Actions page:
    - Opens page
    - Types ticker
    - Selects first autocomplete suggestion
    - Downloads CSV
    """

    url = "https://www.nseindia.com/companies-listing/corporate-filings-actions"

    # Browser options
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("prefs", {
        "download.default_directory": download_folder,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })

    # Start Chrome
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    wait = WebDriverWait(driver, 20)

    try:
        print(f"\n🔎 Opening NSE Corporate Actions page...")
        driver.get(url)

        # --- 1️⃣ Locate search box ---
        search_box = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input.companyVal.companyAutoComplete")
            )
        )

        print(f"🔍 Typing ticker: {ticker}")
        search_box.clear()
        search_box.send_keys(ticker)
        time.sleep(0.8)  # small delay for autocomplete to trigger

        # --- 2️⃣ Wait for dropdown to open ---
        wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div.tt-menu[aria-expanded='true']")
            )
        )

        # --- 3️⃣ Click first suggestion ---
        first_option = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div.tt-menu[aria-expanded='true'] .tt-suggestion")
            )
        )
        print("📌 Selecting first autocomplete option...")
        first_option.click()
        time.sleep(1.5)

        # --- 4️⃣ Click Download CSV ---
        download_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(text(),'Download (.csv)')]")
            )
        )
        print("⬇ Downloading CSV...")
        download_btn.click()

        print(f"✔ CSV download started for {ticker}")

        time.sleep(3)

    except Exception as e:
        print("❌ ERROR:", e)

    finally:
        driver.quit()
        print("🚪 Browser closed.")


# ------------------------------------------------------
# Run the function
# ------------------------------------------------------

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
for stock in nifty50_since_2018:
    download_corporate_actions_csv(stock, download_folder=r"D:\aman\python projects\index_contraction")

len(nifty50_since_2018)
import pandas as pd
import glob

csv_list = glob.glob(r'D:\aman\python projects\index_contraction\corp_event\*.csv')
combined_data = []
for l in csv_list:
        data = pd.read_csv(l)
        data = data[data['PURPOSE'].str.contains(r'(?:Dividend|/Div)')].copy()
        data['payout_per_s'] = data['PURPOSE'].str.extract(r'(?:Rs|Re)[\.\s/-]*([\d\.]+)')
        #df = data[['SYMBOL','EX-DATE','RECORD DATE','payout_per_s']].copy()
        combined_data.append(data)

df = pd.concat(combined_data)
df.to_csv('dividends.csv')
combined_data = []
for _,l in enumerate(csv_list):
     data = pd.read_csv(l)
     combined_data.append(data)


df = pd.concat(combined_data)     
df_split = df[df['PURPOSE'].str.contains(r'(?:Face Value Split)')].copy()
df_split['event_type'] = 'split'
df_split['old_face_value'] = df_split['PURPOSE'].str.extract(r'(?:From Rs|Split Rs)[\.\s/-]*([\d\.]+)')
df_split['new_face_value'] = df_split['PURPOSE'].str.extract(r'(?:To Rs|To Re)[\.\s/-]*([\d\.]+)')
df_bonus = df[df['PURPOSE'].str.contains(r'(?:Bonus)')].copy()
df_bonus['event_type'] = 'bonus'
df_bonus['ratio'] = df_bonus['PURPOSE'].str.extract(r'(?:Bonus)[\.\s/-]*([\d\.]+:[\d\.]+)')



bonus = pd.read_csv('bonus.csv')
split = pd.read_csv('split.csv')

corporate_actions = pd.concat([split,bonus],axis=0)

mask = corporate_actions['event_type'] == 'split'

corporate_actions.loc[mask, 'ratio'] = ('1:' +
    (corporate_actions.loc[mask, 'old_face_value'] /
     corporate_actions.loc[mask, 'new_face_value']).astype(int).astype(str)
)