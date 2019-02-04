import logging
import os
from time import sleep
from typing import List, Dict

import validators
from furl import furl
from pymongo import MongoClient
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


def get_driver(headless: bool = False) -> Chrome:
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


def parse_trade_list_cut(driver: Chrome):
    trade_rows = driver.find_elements_by_xpath("//table[@class='bank']//tbody/tr")[1:]

    page_links = []
    for row in trade_rows:
        try:
            href_value = row.find_elements_by_tag_name('td')[5].find_element_by_tag_name('a').get_attribute('href')
            if validators.url(href_value):
                page_links.append(href_value)
        except Exception as e:
            print(row.get_attribute('outerHTML'))

    return page_links


def get_current_page_number(driver: Chrome) -> int:
    return int(driver.find_element_by_xpath(f'//tr[@class="pager"]//span').text)


def get_trade_links(driver: Chrome) -> List[str]:
    page_number = 2
    trade_links = []
    while True:
        trade_links.extend(parse_trade_list_cut(driver))

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

    return trade_links


def save_trade(trade_card: Dict[str, str]):
    client = MongoClient('localhost:27017')
    db = client['EFRSB']

    trade_cards = db.trade_cards

    trade_cards.insert_one(trade_card)


def parse_field_value(cell: WebElement):
    content_tables = cell.find_elements_by_tag_name('table')
    if content_tables:
        content_table = content_tables[0]
        elem = content_table.find_element_by_tag_name('td')
        return elem.get_attribute('innerText')
    else:
        return cell.get_attribute('innerText')


def parse_trade(driver: Chrome, link: str):
    logger.info(f"Parsing card: {link}")
    driver.get(link)

    trade_card = {}
    trade_card_id = furl(link).query.params['ID']
    trade_card['ID'] = trade_card_id

    print(f"\n\n{link}")

    trade_info_table = driver.find_element_by_id("ctl00_cphBody_tableTradeInfo")
    for tr in trade_info_table.find_elements_by_tag_name('tr'):
        cells = tr.find_elements_by_tag_name('td')
        if len(cells) > 2:
            for i in cells:
                print(i.get_attribute('innerHTML'))
        field_name = cells[0].get_attribute('innerText')
        field_value = parse_field_value(cells[1])
        trade_card[field_name] = field_value

        # print(f"GGGGG: {field_name}")



    trade_lot_info = driver.find_element_by_id('ctl00_cphBody_lvLotList_ctrl0_tblTradeLot')
    for tr in trade_lot_info.find_elements_by_tag_name('tr'):
        cells = tr.find_elements_by_tag_name('td')
        if len(cells) == 2:
            field_name = cells[0].get_attribute('innerText')
            field_value = cells[1].get_attribute('innerText')
        elif len(cells) == 1:
            field_name = cells[0].find_element_by_tag_name('b').get_attribute('innerText')
            field_value = cells[0].find_element_by_tag_name('div').get_attribute('innerText')
        else:
            logger.warning(f'Wrango amount of cells: {link}')
            continue
        # print(field_name)
        if field_name == '':
            logger.warning(f'field_name is empty: field_name == {field_name}, field_value == {field_value}')

        trade_card[field_name] = field_value

    return trade_card


def parse_trades(driver: Chrome, trade_links: List[str]):
    for link in trade_links:
        trade_card = parse_trade(driver, link)
        save_trade(trade_card)

        sleep(1)


def run(*args):
    driver = get_driver(headless=('headless' in args))
    driver.get(EFRSB_URL)

    trade_links = get_trade_links(driver)
    parse_trades(driver, trade_links)

    driver.close()

    print('END')
