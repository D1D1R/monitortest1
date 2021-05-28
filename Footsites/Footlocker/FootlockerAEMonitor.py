# No restocks, only releases
import requests
from datetime import datetime
import json
from bs4 import BeautifulSoup
import urllib3
import time
import logging
import dotenv
from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, HardwareType
from fp.fp import FreeProxy

logging.basicConfig(filename='Footlockerlog.log', filemode='a', format='%(asctime)s - %(name)s - %(message)s', level=logging.DEBUG)

software_names = [SoftwareName.CHROME.value]
hardware_type = [HardwareType.MOBILE__PHONE]
user_agent_rotator = UserAgent(software_names=software_names, hardware_type=hardware_type)
CONFIG = dotenv.dotenv_values()

proxyObject = FreeProxy(country_id=['en_AE'], rand=True)

INSTOCK = []

def test_webhook():
    data = {
        "username": CONFIG['USERNAME'],
        "avatar_url": CONFIG['AVATAR_URL'],
        "embeds": [{
            "title": "Test du Webhook",
            "description": "Si il y a ce message, cela fonctionne! Il faut maintenant le mettre sur un serveur :)",,
            "color": int(CONFIG['COLOUR']),
            "footer": {'text': 'Idir'},
            "timestamp": str(datetime.datetime.utcnow())
        }]
    }

    result = rq.post(CONFIG['WEBHOOK'], data=json.dumps(data), headers={"Content-Type": "application/json"})

    try:
        result.raise_for_status()
    except rq.exceptions.HTTPError as err:
        logging.error(err)
    else:
        print("Données livrées avec succès, code {}.".format(result.status_code))
        logging.info(msg="Données livrées avec succès, code {}.".format(result.status_code))


def discord_webhook(title, thumbnail, url, price, colour):
    """
    Envoyé une notification discord webhook à l'URL dedié
    """
    data = {
        "username": CONFIG['USERNAME'],
        "avatar_url": CONFIG['AVATAR_URL'],
        "embeds": [{
            "title": title,
            "thumbnail": {"url": thumbnail},
            "url": f'https://www.footlocker.ae/en/{url}'
            "color": int(CONFIG['COLOUR']),
            "footer": {'text': '---------'},
            "timestamp": str(datetime.utcnow())
            "fields": [
                {"name": "Colour", "value": colour},
                {"name": "Price": "value": price}
            ]
        }]
    }

    result = requests.post(CONFIG['WEBHOOK'], data=json.dumps(data), headers={"Content-Type": "application/json"})

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        logging.error(msg=err)
    else:
        print("Données livrées avec succès, code {}.".format(result.status_code))
        logging.info("Données livrées avec succès, code {}.".format(result.status_code))


def checker(item):
    """
    Détermine si le statut du produit a changé
    """
    for product in INSTOCK:
        if product == item:
            return True
    return False


def scrape_main_site(headers, proxy):
    """
    Scrape le site Footlocker et ajouter chaque élément à un tableau
    """
    items = []
    s = requests.Session()
    url = 'https://www.footlocker.ae/en/shop-mens/shoes/'
    html = s.get(url=url, headers=headers, proxies=proxy, verify=False, timeout=10)
    soup = BeautifulSoup(html.text, 'html.parser')
    array = soup.find_all('div', {'class': 'fl-category--productlist--item'})
    for i in array:
        item = [i.find('span', {'class': 'ProductName-primary'}).text,
                i.find('span', {'class': 'ProductName-alt'}).text.split(chr(8226))[0],
                i.find('span', {'class': 'ProductName-alt'}).text.split(chr(8226))[1],
                i.find('img')['src'],
                i.find('a', {'class': 'ProductCard-link ProductCard-content'})['href']]
        items.append(item)

    logging.info(msg='Le site à bien été Scrap')
    s.close()
    return items


def remove_duplicates(mylist):
    """
    Supprime les valeurs doubles d’une liste
    """
    return [list(t) for t in set(tuple(element) for element in mylist)]


def comparitor(item, start):
    if checker(item):
        pass
    else:
        INSTOCK.append(item)
        if start == 0:
            print(item)
            discord_webhook(
                title='',
                thumbnail='',
                url='',
                price='',
                colour=''
            )


def monitor():
    """
    Lance le contrôle
    """
    print('Vroum Vroum..! Ca demarre')
    logging.info(msg='La machine est lancé!')
    test_webhook()
    start = 1
    proxy_no = 0

    proxy_list = CONFIG['PROXY'].split('%')
    proxy = {"http": proxyObject.get()} if proxy_list[0] == "" else {"http": f"http://{proxy_list[proxy_no]}"}
    headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}
    keywords = CONFIG['KEYWORDS'].split('%')
    while True:
        try:
            items = remove_duplicates(scrape_main_site(headers, proxy))
            for item in items:
                check = False
                if keywords == "":
                    comparitor(item, start)
                else:
                    for key in keywords:
                        if key.lower() in item[0].lower():
                            check = True
                            break
                    if check:
                        comparitor(item, start)
            start = 0
            time.sleep(float(CONFIG['WEBHOOK']))
        except Exception as e:
            print(f"Exception trouvé '{e}' - Rotation 'proxy' et 'user-agent'")
            logging.error(e)
            headers = {'User-Agent': user_agent_rotator.get_random_user_agent()}
            if CONFIG['PROXY'] == "":
                proxy = {"http": proxyObject.get()}
            else:
                proxy_no = 0 if proxy_no == (len(proxy_list) - 1) else proxy_no + 1
                proxy = {"http": f"http://{proxy_list[proxy_no]}"}


if __name__ == '__main__':
    urllib3.disable_warnings()
    monitor()
