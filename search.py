import datetime
import os
import time

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

DB_CONNECT = {
    'dbname': os.environ['db_name'],
    'host': os.environ['db_host'],
    'port': os.environ['db_port'],
    'user': os.environ['db_user'],
    'password': os.environ['db_password']
}

HEADER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 YaBrowser/20.9.3.136 Yowser/2.5 Safari/537.36"}


def add_case(case_name, case_quantity, average_purchase_price, user_id):  # добавление кейса

    conn = None
    count_raws = 5

    try:
        conn = psycopg2.connect(**DB_CONNECT)

        with conn.cursor() as curs:
            curs.execute(
                f"SELECT COUNT(*) "
                f"FROM user_case "
                f"WHERE user_id = '{user_id}';")  # получаем количество записей по user_id
            count_raws = curs.fetchone()[0]
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return 'Ошибка сервера'
    finally:
        if conn is not None:
            conn.close()

    if count_raws > 4:  # в портфеле может быть не более 5 записей
        # print('Достигнут максимальный размер портфеля')
        return 'В портфеле может быть не более 5 наименований кейсов'
    else:
        conn = None

        response = requests.get(
            fr'https://steamcommunity.com/market/priceoverview/?currency=5&country=ru&appid=730&market_hash_name={case_name}&format=json',
            headers=HEADER).json()

        if response['success'] and response['lowest_price']:
            try:
                conn = psycopg2.connect(**DB_CONNECT)  # подключаемся к БД

                with conn.cursor() as curs:
                    curs.execute(
                        f"SELECT * "
                        f"FROM steam_case "
                        f"WHERE case_name = '{case_name}';")  # проверяем наличие кейса в steam_case
                    result_steam_case = curs.fetchone()

                    if result_steam_case:
                        # print('Кейс уже есть в таблице')
                        pass
                    else:
                        price = response['lowest_price'].split()[0].replace(',', '.')
                        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        curs.execute(
                            f"INSERT INTO steam_case (case_name, case_price, update_timestamp) "
                            f"VALUES ('{case_name}', {price}, '{timestamp}');")  # добавляем новый кейс в steam_case
                        # print('Кейс успешно добавлен')

                    curs.execute(
                        f"SELECT id "
                        f"FROM steam_case "
                        f"WHERE case_name = '{case_name}';")  # узнаем id кейса (меньше запросов)
                    current_case_id = curs.fetchone()[0]

                    curs.execute(
                        f"SELECT * "
                        f"FROM user_case "
                        f"WHERE user_id = '{user_id}' AND case_name = '{current_case_id}';")  # проверяем наличие кейса в портфеле пользователя
                    # curs.execute(
                    #     f"SELECT * "
                    #     f"FROM user_case "
                    #     f"WHERE user_id = '{user_id}' AND case_name = ("
                    #     f"SELECT steam_case.id "
                    #     f"FROM steam_case "
                    #     f"WHERE case_name = '{case_name}');")

                    result_user_case = curs.fetchone()

                    if result_user_case:
                        conn.commit()
                        # print('Кейс уже в портфеле')

                        return 'Кейс уже в портфеле'
                    else:
                        curs.execute(
                            f"INSERT INTO user_case (user_id, case_name, case_quantity, average_purchase_price) "
                            f"VALUES ('{user_id}', '{current_case_id}', '{case_quantity}', '{average_purchase_price}');")  # добавляем кейс в портфель
                        # curs.execute(
                        #     f"INSERT INTO user_case (user_id, case_name, case_quantity, average_purchase_price) "
                        #     f"VALUES ('{user_id}', "
                        #     f"(SELECT steam_case.id "
                        #     f"FROM steam_case "
                        #     f"WHERE case_name = '{case_name}'), '{case_quantity}', '{average_purchase_price}');")
                        conn.commit()

                        # print('Кейс добавлен в портфель')
                        return 'Кейс добавлен в портфель'
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)
                return 'Ошибка сервера'
            finally:
                if conn is not None:
                    conn.close()
        else:
            return 'Кейс не найден в Steam'


""""""


def remove_case(user_id, case_name):  # удаление кейса
    conn = None
    rows_deleted = 0

    try:
        conn = psycopg2.connect(**DB_CONNECT)  # подключаемся к БД

        with conn.cursor() as curs:
            curs.execute(
                f"DELETE FROM user_case "
                f"USING steam_case "
                f"WHERE user_case.user_id = '{user_id}' "
                f"AND user_case.case_name = steam_case.id "
                f"AND steam_case.case_name = '{case_name}';")  # удаляем кейс из портфолио
            rows_deleted = curs.rowcount  # количество удаленных строк
            conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return 'Ошибка сервера'
    finally:
        if conn is not None:
            conn.close()

    if rows_deleted > 0:
        # print('Записей удалено:', rows_deleted)
        return 'Кейс удален'
    else:
        return 'Кейс не найден'


""""""


def show_info(user_id):  # показ портфеля
    conn = None

    try:
        conn = psycopg2.connect(**DB_CONNECT)

        with conn.cursor() as curs:
            curs.execute(
                f"SELECT user_case.id, user_id, steam_case.case_name, case_quantity, average_purchase_price, steam_case.update_timestamp "
                f"FROM user_case "
                f"JOIN steam_case ON user_case.case_name = steam_case.id "
                f"WHERE user_case.user_id = '{user_id}' "
                f"ORDER BY user_case.id;")  # получаем все записи по user_id

            raws_count = curs.rowcount

            if raws_count > 0:
                result = curs.fetchall()

                for i in result:
                    if int(time.time()) - int(i[5].timestamp()) > 300:  # если разница > 300 секунд, цены обновляются
                        time.sleep(0.5)
                        response = requests.get(
                            fr'https://steamcommunity.com/market/priceoverview/?currency=5&country=ru&appid=730&market_hash_name={i[2]}&format=json',
                            headers=HEADER).json()
                        if response['success'] and response['lowest_price']:
                            new_price = response['lowest_price'].split()[0].replace(',', '.')
                            curs.execute(
                                f"UPDATE steam_case "
                                f"SET case_price = '{new_price}', update_timestamp = '{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}' "
                                f"WHERE case_name = '{i[2]}'")  # обновление цены

                            print(f'Цена кейса {i[2]} обновлена')
            else:
                return 'Записей не найдено'

        with conn.cursor() as curs:
            curs.execute(
                f"SELECT user_case.id, user_id, steam_case.case_name, case_quantity, average_purchase_price, steam_case.case_price, steam_case.update_timestamp "
                f"FROM user_case "
                f"JOIN steam_case ON user_case.case_name = steam_case.id "
                f"WHERE user_case.user_id = '{user_id}' "
                f"ORDER BY user_case.id;")  # получаем обновленные записи по user_id

            result = curs.fetchall()

        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return 'Ошибка сервера'
    finally:
        if conn is not None:
            conn.close()

    if len(result) > 0:
        # print(result)
        return result
    else:
        return 'Записей не найдено'
