import logging
import os
from time import sleep
from typing import List

import validators
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome, ChromeOptions, DesiredCapabilities
from selenium.webdriver.remote.webelement import WebElement

EFRSB_URL = 'https://bankrot.fedresurs.ru/TradeList.aspx'

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='./logs/log')
logger = logging.getLogger('efrsb_parser')
logger.setLevel(logging.INFO)


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


def parse_bidding_list_cut(driver: Chrome):
    bidding_rows = driver.find_elements_by_xpath("//table[@class='bank']//tbody/tr")[1:]

    page_links = []
    for row in bidding_rows:
        try:
            href_value = row.find_elements_by_tag_name('td')[5].find_element_by_tag_name('a').get_attribute('href')
            if validators.url(href_value):
                page_links.append(href_value)
        except Exception as e:
            print(row.get_attribute('outerHTML'))

    return page_links


def get_current_page_number(driver: Chrome) -> int:

    return int(driver.find_element_by_xpath(f'//tr[@class="pager"]//span').text)


def get_bidding_links(driver: Chrome) -> List[str]:
    page_number = 2
    bidding_links = []
    while True:
        bidding_links.extend(parse_bidding_list_cut(driver))

        pager = driver.find_element_by_class_name('pager')
        try:
            pager.find_element_by_xpath(f'//tr[@class="pager"]//a[text()="{page_number}"]').click()
            sleep(1)
        except NoSuchElementException:
            last_page_link = pager.find_elements_by_tag_name('a')[-1]
            if last_page_link.text == '...':
                last_page_link.click()
            else:
                break

        # здесь fact_page_number - это фактический номер страницы,
        # в то время как просто page_number - это рассчётный номер
        fact_page_number = get_current_page_number(driver)
        logger.info(f'Current page: {fact_page_number}')

        page_number += 1
        sleep(1)

        break  # !!! пока смотрим только первую страницу

    return bidding_links


def parse_biddings(driver: Chrome, bidding_links: List[str]):
    for link in bidding_links:
        print(link)
        driver.get(link)
        sleep(1)


def run(*args):
    driver = get_driver(headless=('headless' in args))
    driver.get(EFRSB_URL)

    bidding_links = get_bidding_links(driver)
    parse_biddings(driver, bidding_links)


    driver.close()

    print('END')
