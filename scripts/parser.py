import os
from time import sleep

from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome, ChromeOptions, DesiredCapabilities


EFRSB_URL = 'https://bankrot.fedresurs.ru/TradeList.aspx'


def get_driver() -> Chrome:
    options = ChromeOptions()

    capabilities = DesiredCapabilities.CHROME
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    if os.environ.get('SITE_WALKER_HOST') != 'DEV':
        options.add_argument("--headless")

    return Chrome("./webdriver/chromedriver", options=options,
                  desired_capabilities=capabilities)


def run():
    driver = get_driver()
    driver.get(EFRSB_URL)

    page_number = 1
    while True:
        driver.find_element_by_class_name('pager')
