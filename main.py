import locale
import os
from decimal import Decimal

import telebot
from dotenv import load_dotenv

from search import add_case, remove_case, show_info

load_dotenv()

TOKEN = os.environ['token']
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start_command(message):
    start_message = (f'<b>Steam Inventory Bot</b>'
                     f'\n\nБот отображает цены на кейсы Counter-Strike и профит по портфелю. Цены обновляются раз в 5 минут'
                     f'\n\nКоманды:'
                     f'\n/start — выводит информацию по боту'
                     f'\n/add — добавляет кейс'
                     f'\n/remove — удаляет кейс'
                     f'\n/info — выводит краткую информацию'
                     f'\n/fullinfo — выводит подробную информацию')

    bot.send_message(message.chat.id, start_message, parse_mode='HTML')


@bot.message_handler(commands=['add'], content_types=['text'])
def _add_case(message):
    if len(message.text.split()) > 3:
        case_info = message.text.split()[1:]
        case_name = case_info[:-2]
        case_quantity = case_info[-2]
        average_purchase_price = case_info[-1]

        mess_checker = message_checker(case_name, case_quantity, average_purchase_price)

        if mess_checker == 'ok':
            result = add_case(case_name=' '.join(case_name).title(), case_quantity=case_quantity,
                              average_purchase_price=average_purchase_price, user_id=message.chat.id)
            bot.send_message(message.chat.id, result)
        else:
            bot.send_message(message.chat.id, mess_checker)
    else:
        bot.send_message(message.chat.id,
                         f'Команда /add должна содержать название кейса, количество и среднюю цену кейса (в рублях):'
                         f'\n\n/add Revolution Case 150 27.43'
                         f'\n/add Chroma Case 23 14.5')


@bot.message_handler(commands=['remove'], content_types=['text'])
def _remove_case(message):
    if len(message.text.split()) > 1:
        case_name = message.text.split()[1:]

        mess_checker = message_checker(case_name)

        if mess_checker == 'ok':
            result = remove_case(user_id=message.chat.id, case_name=' '.join(case_name).title())

            bot.send_message(message.chat.id, result)
        else:
            bot.send_message(message.chat.id, mess_checker)
    else:
        bot.send_message(message.chat.id, f'Команда /remove должна содержать название кейса:'
                                          f'\n\n/remove Revolution Case')


@bot.message_handler(commands=['info'], content_types=['text'])
def _show_info(message):  # основная информация по портфелю
    if len(message.text.split()) > 1:
        pass
    else:
        bot.send_message(message.chat.id, 'Обновление...')
        result_raw = show_info(message.chat.id)
        if result_raw == 'Записей не найдено':
            bot.send_message(message.chat.id, result_raw)
        else:
            result = result_to_str(result_raw)
            bot.send_message(message.chat.id, result, parse_mode='HTML')


@bot.message_handler(commands=['fullinfo'], content_types=['text'])
def _show_full_info(message):  # полная информация по портфелю
    if len(message.text.split()) > 1:
        pass
    else:
        bot.send_message(message.chat.id, 'Обновление...')
        result_raw = show_info(message.chat.id)
        if result_raw == 'Записей не найдено':
            bot.send_message(message.chat.id, result_raw)
        else:
            result = result_to_str(result_raw, full_info=True)
            bot.send_message(message.chat.id, result, parse_mode='HTML')


def message_checker(case_name, case_quantity=None, average_purchase_price=None):  # проверка на валидность
    if all(x.isalnum() for x in case_name):  # название кейса должно состоять из букв и цифр
        # print('Название корректно')
        pass
    else:
        return 'Название кейса указано неверно'

    if case_quantity:
        if case_quantity.isdigit():  # количество из цифр
            # print('Количество корректно')
            pass
        else:
            return 'Количество кейсов указано неверно'

    if average_purchase_price:
        try:
            float(average_purchase_price)  # средняя цена из цифр (int или float)
        except ValueError:
            return 'Средняя цена кейса указана неверно'
        else:
            # print('Средняя цена корректна')
            pass

    return 'ok'


def result_to_str(result_raw, full_info=False):  # результат в строку
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    result = ''
    start_sum = 0
    current_sum = 0

    if full_info:  # подробная информация по портфелю
        result += '<b>Подробная информация по портфелю:</b>\n'

        for i in result_raw:  # [id, user_id, case_name, case_quantity, average_purchase_price, case_price, update_timestamp]
            current_case = (
                f"\n<b>{i[2]}</b>"
                f"\nКол-во: {i[3]}"
                f"\nЦена покупки: {locale.currency(i[4], grouping=True)}"
                f"\nСтоимость покупки: {locale.currency(i[4] * i[3], grouping=True)}"
                f"\nТекущая цена: {locale.currency(i[5], grouping=True)}"
                f"\nТекущая стоимость: {locale.currency(i[5] * i[3], grouping=True)}\n")

            start_sum += i[4] * i[3]
            current_sum += i[5] * i[3]
            result += current_case

        fee = Decimal('0.13')  # комиссия Steam

        result += '\n==='
        result += f'\n\nОбщая стоимость покупки: {locale.currency(start_sum, grouping=True)}'
        result += f'\nОбщая текущая стоимость: {locale.currency(current_sum, grouping=True)}'
        result += f'\nКомиссия Steam (13%): {locale.currency(current_sum * fee, grouping=True)}'

    else:  # краткая информация по портфелю
        result += '<b>Краткая информация по портфелю:</b>\n'

        for i in result_raw:
            start_sum += i[4] * i[3]
            current_sum += i[5] * i[3]
            result += f"\n{i[2]}"

        result += f'\n\n==='

    profit = (current_sum * Decimal('0.87')) - start_sum
    if profit > 0:
        result += f'\n\n✅ <b>Профит (с учетом комиссии):</b> {locale.currency(profit, grouping=True)}'
    else:
        result += f'\n\n❌ <b>Профит (с учетом комиссии):</b> {locale.currency(profit, grouping=True)}'

    return result


bot.infinity_polling()
