import logging
from time import sleep
from typing import List, Dict, Tuple

import validators
from furl import furl
from pymongo import MongoClient
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome, ChromeOptions, DesiredCapabilities
from selenium.webdriver.remote.webelement import WebElement

from efrsb_parser.settings import MONGO_HOST, MONGO_PORT

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
    options.add_argument("--window-position=1920,50")
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
            href_value = row.find_elements_by_tag_name('td')[5].find_element_by_tag_name('a')\
                                                               .get_attribute('href')
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


def save_trade_card(trade_card: Dict[str, str]):
    client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    db = client['EFRSB']

    result = db.trade_cards.update_one({'id': trade_card['id']}, {'$set': trade_card}, upsert=True)
    print(result.raw_result)
    print(result.upserted_id)
    print(result.matched_count)


def parse_row(tr: WebElement) -> Tuple[str, str]:
    """Use for parsing trade card or lot card"""
    cells = tr.find_elements_by_xpath('./td')
    if len(cells) == 2:
        field_name = cells[0].get_attribute('innerText').replace('.', ' ').strip()

        inner_tables = cells[1].find_elements_by_tag_name('table')
        if inner_tables:
            '''Бывает, что ячейка содержит историю изменений в виде table '''
            field_value = inner_tables[0].find_element_by_tag_name('td').get_attribute('innerText')
        else:
            field_value = cells[1].get_attribute('innerText')
    elif len(cells) == 1:
        field_name = cells[0].find_element_by_tag_name('b').get_attribute('innerText').strip()
        field_value = cells[0].find_element_by_tag_name('div').get_attribute('innerText')
    else:
        raise ValueError(f'Wrang amount of cells')

    return field_name, field_value


def parse_lots(driver: Chrome, trade_card_id) -> List[dict]:
    lots = []
    for lot_div in driver.find_elements_by_xpath('//*[@id="ctl00_cphBody_rpvLots"]/div'):
        lot = {'TRADE_CARD_ID': trade_card_id}
        for tr in lot_div.find_elements_by_xpath('./table//tr'):
            field_name, field_value = parse_row(tr)

            if field_name == '' and field_value != '':
                raise ValueError(f'field_name is empty: {tr.get_attribute("outerHTML")}')

            if field_name != '':
                lot[field_name] = field_value

        lots.append(lot)

    return lots


def parse_trade_card(driver: Chrome, link: str):
    logger.info(f"Parsing card: {link}")
    driver.get(link)

    trade_card = {}
    trade_card_id = furl(link).query.params['ID']
    trade_card['id'] = trade_card_id

    print(f"\n\n{link}")
    for tr in driver.find_elements_by_xpath('//*[@id="ctl00_cphBody_tableTradeInfo"]/tbody/tr'):
        field_name, field_value = parse_row(tr)
        trade_card[field_name] = field_value

    lot_list = parse_lots(driver, trade_card_id)

    return trade_card, lot_list


def parse_trade_cards(driver: Chrome, trade_links: List[str]):
    for link in trade_links:
        try:
            trade_card, lots = parse_trade_card(driver, link)
            save_trade_card(trade_card)
        except Exception as e:
            logger.exception(e)
            raise e

        sleep(1)


def run(*args):
    driver = get_driver(headless=('headless' in args))
    driver.get(EFRSB_URL)

    trade_links = get_trade_links(driver)
    parse_trade_cards(driver, trade_links)

    driver.close()

    print('END')
