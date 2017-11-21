from lxml import html
import requests
from requests_futures.sessions import FuturesSession
from bs4 import BeautifulSoup
import re


# Base urls
BASE_URL = 'http://paizo.com/pathfinderRPG/prd/coreRulebook/'
SPELL_LIST = 'spellLists.html'

# Spell range to fetch
FIRST_SPELL = 663
LAST_SPELL = 1052

# RegEx
SPELL_RESISTANCE_REGEX = re.compile('(Spell Resistance y)')
COMPONENTS_REGEX = re.compile('(Components?:? [VSM])( \(.*\))?(, [SMF])?( \(.*\))?(, [MDF])?( \(.*\))?')
LEVEL_REGEX = re.compile('wizard [0-9]')
TITLE_CLASS_REGEX = re.compile('stat-block-title')


def get_components(components: str):
    component_list = []
    if 'V' in components:
        component_list.append('V')
    if 'S' in components:
        component_list.append('S')
    if 'M' in components:
        component_list.append('M')
    if 'F' in components:
        component_list.append('F')
    return component_list


def get_level_association(html_content: str):
    title_matches = TITLE_CLASS_REGEX.finditer(html_content)
    level_list = []
    for title in title_matches:
        added_level = False
        level_matches = LEVEL_REGEX.finditer(html_content)
        for level in level_matches:
            if title.end() < level.start() <= title.end() + 200:
                level_list.append(int(level.group()[7:]))
                added_level = True

        if not added_level:
            level_list.append(-1)

    return level_list


session = FuturesSession()
async_requests = []
opened_urls = []

for spell_number in range(FIRST_SPELL, LAST_SPELL + 1):
    page = requests.get(BASE_URL + SPELL_LIST)
    tree = html.fromstring(page.content)
    spell_page = tree.xpath('/html/body/div[2]/div[2]/p[' + str(spell_number) + ']/b/a/@href')[0]
    url = (BASE_URL + spell_page).split('#')[0]
    if url not in opened_urls:
        opened_urls.append(url)
        async_requests.append({
            'request': session.get(url),
            'url': url
        })

all_spells = []

for request in async_requests:
    raw_html = request['request'].result().content
    soup = BeautifulSoup(raw_html, 'lxml')
    text = soup.body.get_text()

    spell_titles = soup.find_all("p", class_="stat-block-title")
    component_str = COMPONENTS_REGEX.search(text)
    spell_resistance = True if SPELL_RESISTANCE_REGEX.search(text) is not None else False
    components = get_components(component_str.group()[11:] if component_str is not None else "")
    levels = get_level_association(str(soup))

    for i in range(len(spell_titles)):
        print(spell_titles[i].text + " " + str(components))
        if levels[i] != -1:
            spell_info = {
                'name': spell_titles[i].text,
                'level': levels[i],
                'components': components,
                'spell_resistance': spell_resistance,
            }
            all_spells.append(spell_info)
