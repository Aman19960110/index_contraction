import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def download_corporate_actions_csv(ticker):
    url = "https://www.nseindia.com/companies-listing/corporate-filings-actions"

    # Setup Chrome options for auto-download
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("prefs", {
        "download.default_directory": r"C:\Users\YourUserName\Downloads",  # change if needed
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)

        wait = WebDriverWait(driver, 20)

        # 1️⃣ Click the search box
        search_box = wait.until(EC.presence_of_element_located((By.ID, "searchCompany")))
        search_box.clear()

        # 2️⃣ Enter ticker
        search_box.send_keys(ticker)
        time.sleep(2)

        # NSE search suggestions popup → press ENTER
        search_box.send_keys(Keys.ENTER)
        time.sleep(2)

        # 3️⃣ Click the "Download (.csv)" button
        download_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[contains(text(), 'Download (.csv)')]")
        ))
        download_btn.click()

        print(f"✔ CSV download started for {ticker}")

        time.sleep(5)

    except Exception as e:
        print("❌ Error:", e)
    finally:
        driver.quit()


# Run the function
download_corporate_actions_csv("INFY")   # change ticker
