import os
from time import sleep

from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome, ChromeOptions, DesiredCapabilities


EFRSB_URL = 'https://bankrot.fedresurs.ru/TradeList.aspx'


def get_driver(headless: bool =False) -> Chrome:
    options = ChromeOptions()

    capabilities = DesiredCapabilities.CHROME
    options.add_argument("--window-position=1920,50")
    options.add_argument("--window-size=1920,1000")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    if headless:
        options.add_argument("--headless")

    return Chrome("./webdriver/chromedriver", options=options,
                  desired_capabilities=capabilities)


def run(*args):
    driver = get_driver(headless=('headless' in args))
    driver.get(EFRSB_URL)

    page_number = 1
    while True:
        pager = driver.find_element_by_class_name('pager')
        try:
            _page = pager.find_element_by_xpath('//tr[@class="pager"]//a[contains(text(), "{}")]'.format(page_number))
            _page.click()

        except NoSuchElementException:
            pager.find_elements_by_tag_name('a')[-1].click()

        page_number += 1
        sleep(1)
