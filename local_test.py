import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from main import scraper1
from main import scraper

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

url = "https://ebill.grayson-collin.coop/maps/ext/OutageWebMap/"
driver.get(url)
time.sleep(10)

print("Page title:", driver.title)
driver.save_screenshot("grayson_collin_screenshot.png")

with open("grayson_collin_source.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

print("Saved screenshot and page source.")
time.sleep(15)
driver.quit()
