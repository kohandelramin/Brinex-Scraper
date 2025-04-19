
# Brinex Scraper

import os
import time
from datetime import datetime
from urllib.parse import urljoin

import pandas as pd
import requests
import gspread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from oauth2client.service_account import ServiceAccountCredentials

# Constants (loaded from environment or .env file)
LOGIN_URL = "https://b2b.brinex.ru/login"
KEYWORDS = os.getenv("SCRAPE_KEYWORDS", "BrandA,BrandB,BrandC").split(',')
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
GOOGLE_SCRIPT_URL = os.getenv("GOOGLE_SCRIPT_URL")
USERNAME = os.getenv("BRINEX_USERNAME")
PASSWORD = os.getenv("BRINEX_PASSWORD")
JSON_CREDENTIAL_PATH = os.getenv("GOOGLE_SERVICE_JSON")


# Google Sheets Authentication
def connect_to_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_CREDENTIAL_PATH, scope)
    return gspread.authorize(creds)


def save_keyword_data(keyword, data_list):
    client = connect_to_google_sheets()
    spreadsheet = client.open(SPREADSHEET_NAME)
    sheet_name = f"{keyword}-scrapy"

    try:
        sheet = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="10")
        sheet.append_row(["Product Name", "Available Stock", "Date", "Keyword"])

    existing_rows = sheet.get_all_values()
    existing_keys = {(row[0], row[2]) for row in existing_rows[1:] if len(row) >= 3}
    new_rows = [row for row in data_list if (row[0], row[2]) not in existing_keys]

    if new_rows:
        sheet.append_rows(new_rows, value_input_option="USER_ENTERED")
        print(f"✅ Saved {len(new_rows)} new rows to '{sheet_name}'")
        return True
    else:
        print(f"ℹ️ No new rows to save for '{sheet_name}'")
        return False


def notify_google_script(sheet_names):
    def send():
        try:
            sheet_param = ",".join(sheet_names)
            response = requests.get(GOOGLE_SCRIPT_URL, params={"sheet": sheet_param})
            if response.status_code == 200:
                print("📧 Email triggered successfully.")
            else:
                print(f"❌ Script error: {response.text}")
        except Exception as e:
            print(f"❌ Failed to call Apps Script: {e}")

    print("❓ Send email notification? (y/n): ", end="", flush=True)
    if input().strip().lower() == 'y':
        send()
    else:
        print("🚫 Email not sent by user choice.")


def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def login(driver):
    driver.get(LOGIN_URL)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "input")))
    driver.find_element(By.XPATH, "//label[contains(text(), 'Логин')]/following-sibling::div//input").send_keys(USERNAME)
    driver.find_element(By.XPATH, "//label[contains(text(), 'Пароль')]/following-sibling::div//input").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//span[contains(text(), 'Войти')]").click()
    time.sleep(5)


def scrape_keyword(driver, keyword, current_date):
    search_url = f"https://b2b.brinex.ru/search-result?find={keyword}"
    driver.get(search_url)
    time.sleep(3)
    keyword_data = []

    while True:
        products = driver.find_elements(By.XPATH, "//div[contains(@class, 'listing-view-table-product')]")
        if not products:
            break

        for product in products:
            try:
                name = product.find_element(By.XPATH, ".//div[contains(@class, 'model')]//div[contains(@class, 'text')]").text.strip()
                stock = product.find_element(By.XPATH, ".//div[contains(@class, 'stock')]//input").get_attribute("aria-valuemax")
                keyword_data.append([name, stock, current_date, keyword])
            except Exception:
                continue

        try:
            next_btn = driver.find_element(By.XPATH, "//button[contains(@class, 'btn-next')]")
            if next_btn.get_attribute("aria-disabled") == "true":
                break
            driver.execute_script("arguments[0].scrollIntoView();", next_btn)
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-next')]")))
            ActionChains(driver).move_to_element(next_btn).click().perform()
            time.sleep(3)
        except:
            break

    return keyword_data


if __name__ == "__main__":
    driver = initialize_driver()
    updated_sheets = []

    try:
        login(driver)
        current_date = datetime.now().strftime("%Y-%m-%d")

        for keyword in KEYWORDS:
            print(f"🔍 Scraping: {keyword}")
            data = scrape_keyword(driver, keyword, current_date)
            if data:
                if save_keyword_data(keyword, data):
                    updated_sheets.append(f"{keyword}-scrapy")

        if updated_sheets:
            notify_google_script(updated_sheets)
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()
