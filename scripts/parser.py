import os
from time import sleep

from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome, ChromeOptions, DesiredCapabilities
from selenium.webdriver.remote.webelement import WebElement

EFRSB_URL = 'https://bankrot.fedresurs.ru/TradeList.aspx'


def get_driver(headless: bool =False) -> Chrome:
    options = ChromeOptions()

    capabilities = DesiredCapabilities.CHROME
    # options.add_argument("--window-position=1920,50")
    options.add_argument("--window-size=1920,1000")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    if headless:
        options.add_argument("--headless")

    return Chrome("./webdriver/chromedriver", options=options,
                  desired_capabilities=capabilities)


def parse_bidding_row(bidding_row: WebElement):
    bidding_row.find_elements_by_tag_name('td')[5].find_element_by_tag_name('a').click()


def parse_bidding_list_cut(driver: Chrome):
    bidding_rows = driver.find_elements_by_xpath("//table[@class='bank']//tbody/tr")[1:]

    for row in bidding_rows:
        parse_bidding_row(row)


def run(*args):
    driver = get_driver(headless=('headless' in args))
    driver.get(EFRSB_URL)

    page_number = 2
    while True:
        pager = driver.find_element_by_class_name('pager')
        try:
            pager.find_element_by_xpath(f'//tr[@class="pager"]//a[text()="{page_number}"]').click()

            parse_bidding_list_cut(driver)
        except NoSuchElementException:
            pager.find_elements_by_tag_name('a')[-1].click()

        page_number += 1
        sleep(1)
