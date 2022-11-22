## scripts

* **avito_parser.py** - тестовое задание.
Необходимо распарсить любую страницу с объявлениями Авито и получить из объявлений максимально возможное количество данных сколько получится. (Если есть
проблемы с тем, что авито перебрасывает на капчу, страницу можно закешировать в файл).Получить с сайта ЦБ актуальный курс Евро и добавить в полученную с Авито таблицу цену
на товар в Евро.Полученные данные записать в базу Sqlite и дополнительно вывести в виде отчета в
любой PDF или Html или Excel.
* **myhh.py** - тестовое задание.
Работа с АПИ стороннего сервиса (это может быть hh.ru, youtube, moex.com, любое), должно быть несколько связанных запросов (один запрос на получение чего-то, результат используется в другом запросе)  
*Комментарий*.
Используем API hh.ru для асинхронного получения данных.Согласно ТЗ (должно быть несколько связанных запросов) - отправляем запрос на получение списка вакансий по ключевому слову и региону, затем ассинхронно получаем детальную информацию по каждой вакансии. Ограничил число одновременных подключений 7 (вроде у hh такой лимит) ,чтобы не словить 429 ошибку. Полученный результат записываем в БД.
