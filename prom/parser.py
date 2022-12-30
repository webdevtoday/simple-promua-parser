import logging
import collections
import json
import csv

import bs4
import requests


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('prom')


ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'brand_name',
        'goods_name',
        'url',
    ),
)

HEADERS = (
    'Brand',
    'Product',
    'Link',
)


class Client:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.2 Safari/605.1.15',
            'Accept-Language': 'ru',
        }
        self.result = []

    def load_page(self):
        url = 'https://prom.ua/ua/Muzhskie-svitera-pulovery'
        res = self.session.get(url=url)
        res.raise_for_status()
        return res.text

    def parse_page(self, text: str):
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select(
            '.js-productad[data-advtracking-source="prom:catalog"]')
        for block in container:
            self.parse_block(block=block)

    def parse_block(self, block):
        json_block = block.select_one('script[type="application/ld+json"]')
        if not json_block:
            logger.error('no json_block')
            return

        json_text = json_block.get_text()
        if not json_text:
            logger.error('no json_text')
            return

        product_info = json.loads(json_text)

        url = product_info['url']
        if not url:
            logger.error('no url')
            return

        brand_name = product_info['offers']['seller']['name']
        if not brand_name:
            logger.info(f'no brand_name on {url}')
            return

        goods_name = product_info['name']
        if not goods_name:
            logger.error(f'no goods_name on {url}')
            return

        self.result.append(ParseResult(
            url=url,
            brand_name=brand_name,
            goods_name=goods_name,
        ))

        logger.debug('%s, %s, %s', url, brand_name, goods_name)
        logger.debug('-' * 100)

    def save_result(self):
        path = './prom/test.csv'
        with open(path, 'w') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(HEADERS)
            for item in self.result:
                writer.writerow(item)

    def run(self):
        text = self.load_page()
        self.parse_page(text=text)
        logger.info(f'Received {len(self.result)} elements')
        self.save_result()


if __name__ == '__main__':
    parser = Client()
    parser.run()
