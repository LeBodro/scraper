from lxml import html
from pymongo import MongoClient
from requests_futures.sessions import FuturesSession
from bs4 import BeautifulSoup
import re


# Base urls
BASE_URL = 'https://www.d20pfsrd.com/bestiary/monster-listings/outsiders/angel/'
HOME_URL = ''
XPATH_FORMAT = '//*[@id="ognajaxnav1"]/li[14]/ul/li[5]/ul/li[11]/ul/li[20]/ul/li[%d]/a'  # angels

# Page range to fetch
FIRST_PAGE = 1
LAST_PAGE = 16

# RegEx
SPELL_RESISTANCE_REGEX = re.compile('(Spell Resistance y)')
COMPONENTS_REGEX = re.compile('(Components?:? [VSM])( \(.*\))?(, [SMF])?( \(.*\))?(, [MDF])?( \(.*\))?')
LEVEL_REGEX = re.compile('wizard [0-9]')
TITLE_CLASS_REGEX = re.compile('stat-block-title')


client = MongoClient()
db = client.db


def fetch_pages(base_url, home_url, page_url_format, begin, end):
    session = FuturesSession()
    async_requests = []
    opened_urls = []
    raw_html_content = []

    for page_number in range(begin, end + 1):
        home = session.get(base_url + home_url)  # range begin to end is inclusive
        tree = html.fromstring(home.result().content)
        page_url = tree.xpath(page_url_format % page_number)[0].attrib['href']  # use %d in page_url_format
        if page_url not in opened_urls:
            opened_urls.append(page_url)
            async_requests.append(session.get(page_url))

    for request in async_requests:
        raw_html_content.append({'content': request.result().content})

    return raw_html_content


def fetch_and_save_raw_angels():
    db.raw_angels.delete_many({})
    raw_angels = fetch_pages(BASE_URL, HOME_URL, XPATH_FORMAT, FIRST_PAGE, LAST_PAGE)
    db.raw_angels.insert_many(raw_angels)


def parse(raw_pages):
    for stuff in raw_pages:
        soup = BeautifulSoup(stuff.content, 'lxml')
        text = soup.body.get_text()

        # spell_titles = soup.find_all("p", class_="stat-block-title")
        # spell_resistance = True if SPELL_RESISTANCE_REGEX.search(text) is not None else False

        # for i in range(len(spell_titles)):
        #     print("parse it")
