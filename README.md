# Телеграм-бот [Steam Inventory Bot](https://t.me/xSteamInventoryBot)
- Дает возможность добавлять в портфель названия кейсов 'Counter-Strike' и отслеживать текущие цены в Steam
- Позволяет экономить время, которое затрачивается на ручной поиск актуальной цены на торговой площадке Steam или в инвентаре

## Особенности
- Названия кейсов должны быть на английском языке
- Цены в рублях
- Максимум 5 наименований кейсов в портфеле
- Цена обновляется при выполнении команд `/info` или `/fullinfo` если прошло более 5 минут после предыдущего обновления. Иначе цена берется из БД
- Работает на синхронном telebot и получает данные через requests (steam priceoverview)
- *Проект для портфолио, на больших нагрузках не тестировался, защиты от спама не имеет*

## Команды
- `/start` выводит информацию о боте
- `/add` добавляет кейс в портфель `/add | название_кейса | количество_кейсов | средняя_цена_покупки_в_рублях`
    - `/add chroma 2 case 150 24.17`
    - `/add glove case 35 1.89`
- `/remove` удаляет кейс из портфеля `/remove | название_кейса`
    - `/remove chroma 2 case`
    - `/remove glove case`
- `/info` выводит краткую информацию о портфеле
- `/fullinfo` выводит подробную информацию о портфеле

## Требования
- Python 3.11
- PostgreSQL
- psycopg2-binary
- pyTelegramBotAPI
- python-dotenv
- requests

В БД нужно создать две таблицы:

- **Steam_case** (id PK, название кейса, актуальная цена, дата обновления):
``` sql
CREATE TABLE Steam_case (id serial PRIMARY KEY, case_name VARCHAR(64) UNIQUE, case_price DECIMAL(7,2), update_timestamp TIMESTAMP);
```
- **User_case** (id PK, id пользователя, название кейса FK, количество кейсов, средняя цена покупки кейса):
``` sql
CREATE TABLE User_case (id serial PRIMARY KEY, user_id VARCHAR(64), case_name INTEGER, case_quantity INTEGER, average_purchase_price DECIMAL(7,2), FOREIGN KEY (case_name) REFERENCES Steam_case (id) ON DELETE CASCADE);
```
