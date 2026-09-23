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

url = "https://webapps.jacksonemc.com/nisc/maps/MemberOutageMap/"
# driver.get(url)
# time.sleep(10)

# print("Page title:", driver.title)
# driver.save_screenshot("new_site_screenshot.png")

# with open("new_site_source.html", "w", encoding="utf-8") as f:
#     f.write(driver.page_source)

# print("Saved ss and page source.")

# time.sleep(20)
# driver.quit()
data = scraper(url, driver)

driver.close()
driver.quit()

for key, df in data.items():
    print(f"--- {key} ---")
    print(df.head())
