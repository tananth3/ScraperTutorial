import logging
import json
import pandas as pd
import geopy
import xmltodict
import time
import boto3


from bs4 import BeautifulSoup
from datetime import datetime
from urllib.request import urlopen, Request
from seleniumwire.utils import decode as sw_decode
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver


def timenow():
    return datetime.strftime(datetime.now(), "%m-%d-%Y %H:%M:%S")


# Example: Use selenium for clicking a button
def scraper1(url, driver):
    def fetch():
        print(f"fetching outages from {url}")

        driver.get(url)
        time.sleep(10)

        button = driver.find_elements("xpath", '//*[@id="OMS.Customers Summary"]')

        if button:
            wait = WebDriverWait(driver, 10)
            label = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//*[@id="OMS.Customers Summary"]')
                )
            )
            label.click()
            time.sleep(5)
            page_source = {}
            select_elements = driver.find_elements(By.CLASS_NAME, "gwt-ListBox")
            menu = Select(select_elements[0])
            for idx, option in enumerate(menu.options):
                level = option.text
                menu.select_by_index(idx)
                time.sleep(3)
                page_source.update({f"per_{level}": driver.page_source})
        return page_source

    def parse():
        data = fetch()
        for level, pg in data.items():
            df = _parse(pg)
            data.update({level: df})
        return data

    def _parse(page_source):
        soup = BeautifulSoup(page_source, "html.parser")
        tables = soup.find_all("table")
        # separate rows
        rows = tables[1].find_all("tr")
        header_row = rows[0]
        data_rows = rows[1:]

        # Extract the table header cells
        header_cells = header_row.find_all("th")
        header = [cell.get_text().strip() for cell in header_cells]
        cols = [h for h in header if h != ""]

        # Extract the table data cells
        data = []
        for row in data_rows:
            cells = row.find_all("td")
            data.append([cell.get_text().strip() for cell in cells])

        # Print the table data as a list of dictionaries
        table = [dict(zip(header, row)) for row in data]
        df = pd.DataFrame(table)
        if len(df.columns) > 1:
            df = df[cols]
            df = df.dropna(axis=0)
            df["timestamp"] = timenow()
            # df = df[df["# Out"] != "0"]
        else:
            df = pd.DataFrame()
        # print("Storing info.csv ...")
        # df.to_csv("info.csv")
        return df

    return parse()


# TODO: Implement your scraper function here
# Input: url to scrape, chromedriver
# Output: A dictionary of dataframe, Ex: {"per_county": <pandas dataframe>, "per_zipcode": <pandas dataframe>, ...}
# Scraper 1 is an example
# Attempting from Georgia Power
def scraper(url, driver):
    def fetch():
        print(f"fetching outages from {url}")
        driver.get(url)
        time.sleep(10)

        # Confirmed: panel needs MENU opened first, still need real markup for this button
        menu_button = driver.find_elements(By.XPATH, "//*[contains(text(), 'MENU')]")
        if menu_button:
            menu_button[0].click()
            time.sleep(2)

        # Confirmed real markup: the Summary toggle
        summary_toggle = driver.find_elements(
            By.XPATH,
            "//div[@class='head' and @role='button'][.//span[@class='title' and contains(text(), 'Summary')]]"
        )
        if summary_toggle:
            summary_toggle[0].click()
            time.sleep(2)

        # Confirmed real markup: the "View County" link specifically
        view_county_link = driver.find_elements(
            By.XPATH,
            "//a[@class='row report-link hyperlink-primary'][.//span[contains(text(), 'View County')]]"
        )
        if view_county_link:
            view_county_link[0].click()
            time.sleep(3)

        return driver.page_source

    def parse():
        return {"per_County": _parse(fetch())}

    def _parse(page_source):
        soup = BeautifulSoup(page_source, "html.parser")
        rows = soup.find_all("div", {"role": "row", "data-parent": True})

        records = []
        for row in rows:
            records.append({
                "County": row.find("div", class_="name").get_text(strip=True) if row.find("div", class_="name") else None,
                "Customers Affected": row.find("div", class_="cust-a").get_text(strip=True) if row.find("div", class_="cust-a") else None,
                "Customers Served": row.find("div", class_="cust-s").get_text(strip=True) if row.find("div", class_="cust-s") else None,
                "Outages": row.find("div", class_="n-out").get_text(strip=True) if row.find("div", class_="n-out") else None,
            })

        df = pd.DataFrame(records)
        if len(df) > 0:
            df["timestamp"] = timenow()
        return df

    return parse()


def handler(event, context):
    s3 = boto3.client("s3")
    bucket = "tananthtutorialbucketing"  # TODO: Modify it to your own s3 bucket

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/opt/chrome/chrome"

    driver = webdriver.Chrome(
        executable_path="/opt/chromedriver", chrome_options=options
    )

    url = "https://webapps.jacksonemc.com/nisc/maps/MemberOutageMap/"

    # data = scraper(url, driver)  # TODO: Modify it to your own scraper()
    data = scraper1(url, driver)

    driver.close()
    driver.quit()

    for key, df in data.items():
        current_time = timenow()
        filename = (
            f"Jackson_{key}_{current_time}.csv"  # TODO: Modify it to your filename
        )
        csv_buffer = pd.DataFrame(df).to_csv(index=False)
        s3.put_object(Bucket=bucket, Key=filename, Body=csv_buffer)

    return {
        "statusCode": 200,
        "body": "Successfully Scrap the Jakson EMC!",
    }  # TODO: Modify it to your own message
