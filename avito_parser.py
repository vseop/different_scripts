import openpyxl
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
import sqlite3
from time import time


# Необходимо распарсить любую страницу с объявлениями Авито и получить из объявлений максимально возможное количество
# данных сколько получится. (Если есть проблемы с тем, что авито перебрасывает на капчу, страницу можно закешировать
# в файл)
# Получить с сайта ЦБ актуальный курс Евро и добавить в полученную с Авито таблицу цену на товар в Евро.
# Полученные данные записать в базу Sqlite и дополнительно вывести в виде отчета в любой PDF или Html или Excel

class AvitoParser:

    def __init__(self, url):
        self.session = requests.Session()
        self.session.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
        }
        self.url = url

    @staticmethod
    def cbr_exchange_rates(charcode):
        url = 'https://www.cbr-xml-daily.ru/daily_utf8.xml'
        response = requests.get(url).content
        soup = BeautifulSoup(response, 'xml')
        value = soup.find('CharCode', text=charcode).find_next_sibling('Value').string
        value = value.replace(',', '.')
        return value

    def get_html(self):
        response = self.session.get(self.url)
        return response.text

    def parse_html(self, html):
        products_database = []
        euro_exchange = self.cbr_exchange_rates('EUR')  # текущий курс евро ЦБ
        soup = BeautifulSoup(html, 'lxml')
        container = soup.find_all('div', {'class': 'iva-item-root-_lk9K'})
        for item in container:
            # ссылка
            href = item.find('a', {'class': 'link-link-MbQDP'}).get('href')
            link = f'https://www.avito.ru{href}'

            # заголовок
            title = item.find('h3', {'class': 'title-root-zZCwT'}).string.strip()

            # цена
            try:
                price = item.find('meta', {'itemprop': 'price'}).get('content')
            except Exception:
                price = 0

            # валюта
            currency = item.find('meta', {'itemprop': 'priceCurrency'}).get('content')

            # цена в евро
            try:
                price_eur = Decimal(price) / Decimal(euro_exchange)
                price_eur = price_eur.quantize(Decimal('1.000'))
            except:
                price_eur = 0

            # описание
            try:
                description = item.find('div', {'class': 'iva-item-text-Ge6dR'}).string.strip('\n')
            except Exception:
                description = 'Описание отсутствует'
            description = list(filter(None, map(lambda i: i.strip(), description.split('\n'))))
            description = '\n'.join(description)

            # метро
            try:
                metro = item.select_one('span.geo-icons-uMILt').find_next_sibling('span').string.strip()
            except Exception:
                metro = 'Не указано'

            # доставка
            try:
                delivery = item.select_one('div.delivery-root-LFKPq span').string.strip()
                delivery = ' '.join(delivery.split()[1:])
            except Exception:
                delivery = 'нет'

            # время размещения
            time = item.find('div', {'class': 'date-text-KmWDf'}).string.strip()

            product_data = {
                'link': link,
                'title': title,
                'price_rur': price,
                'price_eur': str(price_eur),
                'description': description,
                'metro': metro,
                'delivery': delivery,
                'time': time,

            }
            products_database.append(product_data)
            # print(product_data)
        return products_database

    @staticmethod
    def save_sql(data):
        with sqlite3.connect(f'{int(time())}.db') as db:
            cursor = db.cursor()
            query = """
            CREATE TABLE avito(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link VARCHAR,
                title VARCHAR,
                price_rur DECIMAL(12,4),
                price_eur DECIMAL(12,4),
                description TEXT,
                metro VARCHAR,
                delivery VARCHAR,
                time VARCHAR
                )"""
            cursor.executescript(query)
            sql1 = """INSERT INTO avito(link, title, price_rur, price_eur, description, metro, delivery, time)
                    VALUES(:link, :title, :price_rur, :price_eur, :description, :metro, :delivery, :time)"""
            cursor.executemany(sql1, data)

    @staticmethod
    def report_excel(data):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Report'
        ws.row_dimensions[1].font = openpyxl.styles.Font(b=True, size=14, color="DD0000")
        ws.append(
            ["Заголовок", "Ссылка", "Цена(руб)", "Цена(евро)", "Метро", "Доставка", "Время размещения", "Описание"])
        for item in data:
            ws.append(
                [item['title'], item['link'], item['price_rur'], item['price_eur'], item['metro'], item['delivery'],
                 item['time'], item['description']])
        ws.auto_filter.ref = "A1:H999"
        ws.column_dimensions['A'].width = 35
        ws.column_dimensions['B'].width = 35
        ws.column_dimensions['E'].width = 25
        ws.column_dimensions['F'].width = 25
        ws.column_dimensions['G'].width = 25
        ws.column_dimensions['H'].width = 35
        wb.save('report.xlsx')


def main():
    url = f'https://www.avito.ru/moskva/telefony'
    p = AvitoParser(url)
    # val = p.cbr_exchange_rates('EUR')
    html = p.get_html()
    data = p.parse_html(html)
    p.save_sql(data)
    p.report_excel(data)


if __name__ == '__main__':
    main()
