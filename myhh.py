import asyncio
import sqlite3

import aiohttp
import requests

# Описание (работа с API hh.ru). Сильно мудрить не стал т.к не было поставленно конкретной задачи.
# Согласно ТЗ (должно быть несколько связанных запросов) - отправляем запрос на получение списка вакансий
# по ключевому слову и региону, затем ассинхронно получаем детальную информацию по каждой вакансии.
# Ограничил число одновременных подключений 7 (вроде у hh такой лимит) ,чтобы не словить 429 ошибку
# Полученный результат записываем в БД.




class Api_hh():
    all_data = []
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36',
    }
    url_list = 'https://api.hh.ru/vacancies'  # api hh

    def __init__(self, text='Data', area=1):
        self.params = {'text': text, 'area': area, 'per_page': 100}

    def get_list_id_vacancies(self):
        """Получаем список id вакансий по нашему запросу"""
        list_id = []
        resp = requests.get(self.url_list, params=self.params, headers=self.headers)
        found = resp.json().get('found')  # кол-во всего найденных вакансий
        print(f'Всего найдено {found} вакансий')
        page_qty = [20, found // 100 + 1][found < 2000] # кол-во страниц max = 20 т.к API не отдает более 2000 вакансий
        print(f'Всего {page_qty} страниц')
        for page in range(page_qty):
            self.params['page'] = page
            resp = requests.get(self.url_list, params=self.params, headers=self.headers)
            assert resp.status_code == 200
            data = resp.json().get('items')
            for vac in data:
                list_id.append(vac.get('id'))

        return list_id

    async def vacancy_id(self, session, vac_id):
        """Асинхронный метод для получения детельной информации по id вакансии"""
        url_id = f'https://api.hh.ru/vacancies/{vac_id}' # api hh
        async with session.get(url_id) as resp:
            assert resp.status == 200
            print(vac_id)
            resp_text = await resp.json()
            self.all_data.append(resp_text)

    async def vacancy_all_id(self, list_id):
        """Создаем сессию и список задач для ассинхронной работы"""
        # Ограничиваем число подключений при помощи TCPConnector, чтобы не словить 429 ошибку
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=7), headers=self.headers) as session:
            tasks = []
            for vac_id in list_id:
                task = asyncio.create_task(self.vacancy_id(session, vac_id))
                tasks.append(task)
            await asyncio.gather(*tasks)

    def save_sql(self, data):
        """Записываем полученные (нужные) данные в БД"""
        with sqlite3.connect('vacancy.db') as db:
            cursor = db.cursor()
            query = f'CREATE TABLE IF NOT EXISTS"{self.params["text"]}"(\
                   id INTEGER,\
                   name_v VARCHAR,\
                   description TEXT,\
                   code_hh INTEGER,\
                   accept_handicapped NUMERIC,\
                   area_v VARCHAR,\
                   employer VARCHAR,\
                   employment VARCHAR,\
                   experience VARCHAR,\
                   schedule_d VARCHAR,\
                   text_search VARCHAR)'

            cursor.executescript(query)
            for value in data:
                cursor.execute(f'INSERT INTO "{self.params["text"]}" (id, name_v, description, code_hh, accept_handicapped,  \
                                 area_v,  employer, employment, experience, schedule_d, text_search)  \
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                               (value['id'], value['name'], value['description'],
                                value['code'], value['accept_handicapped'], value['area']['name'],
                                value['employer']['name'],
                                value['employment']['name'], value['experience']['name'], value['schedule']['name'],
                                self.params['text']))

    def run(self):
        """Собираем все вместе и запускаем"""
        list_id = self.get_list_id_vacancies()
        try:
            asyncio.run(self.vacancy_all_id(list_id))
        except Exception as e:
            print(str(e))

        print('Запись данных в БД')
        self.save_sql(self.all_data)
        print('Все прошло успешно')


if __name__ == '__main__':
    q = Api_hh('developer', 1)
    q.run()
