import asyncio
import requests
import time
import logging
import os
import traceback
from dotenv import load_dotenv

from pprint import pprint
from cachetools import TTLCache
from telebot import types
from telebot.async_telebot import AsyncTeleBot

logging.basicConfig(filename='bot_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='UTF-8')
states = {}
load_dotenv()

turns = {'sell': ['продажу', 'продать', 'продажи', 'приобрести'],
         'buy': ['покупку', 'купить', 'покупки', 'отдать']}
key_bot = os.getenv('EXCHANGE_BOT')
bot = AsyncTeleBot(key_bot)
group_chat_id = os.getenv('EXCHANGE_CHAT')


@bot.message_handler(commands=['start'])
async def start_message(message):
    await bot.send_message(message.from_user.id, """👋 привет!

💎 с помощью этого бота ты сможешь узнать
средние цены (покупки/продажи)
USDT/KZT/RUB/UYU/MAD по информации с бирж

Примечания:
1. Курсы представлены без учёта комиссий
2. Курсы предоставляются в реальном времени
3. Данные курсы являются средним арифметическим 
  последних 10ти ордеров по выбранной валюте.
  На практике курсы могут чуть отличаться.
4. При использовании '/calculate' нужно использовать только цифры
  и по желанию точку для цифр после 'запятой'

main chat t.me/dirhamrubl
exchange chat @SudokuH
""")


@bot.message_handler(commands=['calculate', '777'])
async def start_message(message):
    user_id = message.from_user.id
    # markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if not states.get(user_id):
        states[user_id] = {}
    if message.text == '/777':
        states[user_id]['commission'] = True
    else:
        states[user_id]['commission'] = False
    markup = types.InlineKeyboardMarkup()
    sell_button = types.InlineKeyboardButton("Продать", callback_data='sell')
    buy_button = types.InlineKeyboardButton("Купить", callback_data='buy')
    # btn_my_site = types.InlineKeyboardButton(text='Наш сайт', url='https://habrahabr.ru')
    markup.add(sell_button, buy_button)
    await bot.send_message(message.from_user.id, "Выберите действие:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['buy', 'sell'])
async def process_sell_callback(call):
    try:
        # Обработка нажатия на кнопку "Продать"
        await bot.answer_callback_query(callback_query_id=call.id, text='Минуточку, готовлю список!')
        markup = types.InlineKeyboardMarkup()
        MAD = types.InlineKeyboardButton("MAD", callback_data="MAD")
        RUB = types.InlineKeyboardButton("RUB", callback_data="RUB")
        KZT = types.InlineKeyboardButton("KZT", callback_data="KZT")
        UYU = types.InlineKeyboardButton("UYU", callback_data="UYU")
        USDT = types.InlineKeyboardButton("USDT", callback_data="USDT")
        user_id = call.from_user.id
        markup.add(MAD, RUB, KZT, UYU, USDT)
        states[user_id]['type'] = call.data
        user_type_exc = states[user_id]['type']
        await bot.send_message(call.from_user.id,
                               f"Вы выбрали {turns[user_type_exc][0]}."
                               f" Что хотите {turns[user_type_exc][1]}?",
                               reply_markup=markup)
    except Exception as e:
        logging.error(f"process_sell_callback:\n{e}")


async def process_sale_amount(message, data, user_id):
    # Сохраняем введенную сумму в словаре states[user_id]
    try:
        print(user_id)
        user_id = message.from_user.id
        print(user_id)
        states[message.from_user.id]['sale_amount'] = float(message.text)
        markup = types.InlineKeyboardMarkup()
        MAD = types.InlineKeyboardButton("MAD", callback_data=f"MAD_2{data}")
        RUB = types.InlineKeyboardButton("RUB", callback_data=f"RUB_2{data}")
        KZT = types.InlineKeyboardButton("KZT", callback_data=f"KZT_2{data}")
        UYU = types.InlineKeyboardButton("UYU", callback_data=f"UYU_2{data}")
        USDT = types.InlineKeyboardButton("USDT", callback_data=f"USDT_2{data}")
        val = {"MAD": MAD,
               "RUB": RUB,
               "KZT": KZT,
               "UYU": UYU,
               "USDT": USDT}
        objects_values = [MAD, RUB, KZT, UYU, USDT]
        objects_values.remove(val.get(data))
        markup.add(*objects_values)
        await bot.send_message(message.chat.id,
                               f"Что хотите {turns[states[user_id]['type']][3]} за {data}?",
                               reply_markup=markup)
        print(states)
    except Exception as e:
        logging.error(f"process_sale_amount:\n{e}")


@bot.callback_query_handler(func=lambda call: call.data in ["MAD", "RUB", "KZT", "UYU", "USDT"])
async def process_option1_callback(call):
    try:

        user_id = call.from_user.id

        states[user_id]['first_value'] = call.data
        user_type_exc = states[user_id].get('type')
        # Проверяем состояние пользователя, чтобы знать, что было выбрано ранее
        if user_id in states and user_type_exc in ['buy', 'sell']:
            # Запросим сумму у пользователя
            await bot.send_message(call.message.chat.id, f"Пожалуйста, введите сумму {turns[user_type_exc][2]}:")

            # устанавливаем состояние пользователя на продаваемую валюту
            @bot.message_handler()
            async def wrapped_process_sale_amount(message):
                print(1)
                await process_sale_amount(message, states[user_id]['first_value'], user_id)

        else:
            # Обработка ошибки: пользователь должен сначала выбрать 'sell'
            await bot.send_message(call.message.chat.id, "Пожалуйста, выберите действие перед выбором опции.")
    except Exception as e:
        logging.error(f"process_option1_callback:\n{e}")


@bot.callback_query_handler(func=lambda call: call.data.split('2')[0] in ["MAD_", "RUB_", "KZT_", "UYU_", "USDT_"])
async def final_answer(call):
    try:
        # print(call)
        user_id = call.from_user.id
        r, k = call.data.split('_2')
        commission = states[user_id]['commission']
        rates = await get_final_exchange_rate(getrate=False, commission=commission)
        value1 = k.lower()
        value2 = r.lower()
        asked_rate = 0
        sale_amount = states[user_id]['sale_amount']
        if states[user_id]['type'] == 'buy':
            asked_rate = rates[f'get_sell_{value2}_to_{value1}']
            if 'usdt' == value1:
                digit = sale_amount * asked_rate
                final_answer = round(digit, 3)
            else:
                digit = sale_amount / asked_rate
                final_answer = round(digit, 3)
            print(asked_rate)
            await bot.send_message(call.message.chat.id, f"Вам нужно будет отдать {final_answer} "
                                                         f"{r} за такую сумму {k} ")
        if states[user_id]['type'] == 'sell':
            asked_rate = rates[f'get_sell_{value1}_to_{value2}']
            if 'usdt' == value2:
                digit = sale_amount / asked_rate
                final_answer = round(digit, 3)
            else:
                digit = sale_amount * asked_rate
                final_answer = round(digit, 3)
            print(asked_rate)
            await bot.send_message(call.message.chat.id, f"Вы получите {final_answer} "
                                                         f"{r} за такую сумму {k} ")
        with open("usernames.txt", "a+", encoding="UTF-8") as f:
            f.write(
                '\n' + f'id: {user_id}, username: @{call.from_user.username if call.from_user.username else "None"},'
                       f"\n summ {states[user_id].get('type')} {sale_amount}  "
                       f"{k} за {r} = {final_answer}")
    except Exception as e:
        logging.error(f"final_answer:\n{e, e.args}")


async def get_fiat_exchange_rate(dividend, divisor, getrate):
    divine = dividend / divisor
    # if commission:
    #     divine = divine * 0.965
    if dividend < divisor and getrate:
        divine = 1 / divine
    result = divine

    return result


class AsyncCache:
    def __init__(self, maxsize, ttl):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)

    async def get(self, key):
        return await asyncio.to_thread(self.cache.get, key)

    async def set(self, key, value):
        await asyncio.to_thread(self.cache.__setitem__, key, value)

    async def delete(self, key):
        await asyncio.to_thread(self.cache.__delitem__, key)


# Определите ключ для кеширования
def cache_key(t, commission, getrate):
    return t, commission, getrate


# Создайте асинхронный кеш
async_cache = AsyncCache(maxsize=3, ttl=1000)


async def get_final_exchange_rate(t=None, commission=False, getrate=True):

    try:
        if t in ['/77', '/777']:
            commission = True
    except Exception as e:
        # не лучшая практика, но здесь это не на что не повлияет.
        pass
    cached_value = await async_cache.get((t, commission, getrate))

    if cached_value is not None:
        # Если значение есть в кеше, верните его
        return cached_value
    get_sell_usdt_to_mad = await process_binance(commission, action="SELL", fiat="MAD", bank=["CIHBank"])
    get_sell_mad_to_usdt = await process_binance(commission, action="BUY", fiat="MAD", bank=["CIHBank"])
    get_sell_usdt_to_rub = await process_kucoin(commission, action='BUY', fiat='RUB', bank="SBP")
    get_sell_rub_to_usdt = await process_kucoin(commission, action='SELL', fiat='RUB', bank="SBP")
    get_sell_usdt_to_kzt = await process_binance(commission, action="SELL", fiat="KZT", bank=["KaspiBank"])
    get_sell_kzt_to_usdt = await process_binance(commission, action="BUY", fiat="KZT", bank=["KaspiBank"])
    get_sell_usdt_to_uyu = await process_binance(commission, action="SELL", fiat="UYU", bank=["Prex"])
    get_sell_uyu_to_usdt = await process_binance(commission, action="BUY", fiat="UYU", bank=["Prex"])
    buy = 1
    if commission:
        buy = 1.0075
    get_sell_mad_to_rub = await get_fiat_exchange_rate(get_sell_usdt_to_rub * buy, get_sell_mad_to_usdt, getrate)
    get_sell_mad_to_kzt = await get_fiat_exchange_rate(get_sell_usdt_to_kzt * buy, get_sell_mad_to_usdt, getrate)
    get_sell_mad_to_uyu = await get_fiat_exchange_rate(get_sell_usdt_to_uyu * buy, get_sell_mad_to_usdt, getrate)
    get_sell_rub_to_mad = await get_fiat_exchange_rate(get_sell_usdt_to_mad * buy, get_sell_rub_to_usdt, getrate)
    get_sell_kzt_to_mad = await get_fiat_exchange_rate(get_sell_usdt_to_mad * buy, get_sell_kzt_to_usdt, getrate)
    get_sell_uyu_to_mad = await get_fiat_exchange_rate(get_sell_usdt_to_mad * buy, get_sell_uyu_to_usdt, getrate)
    get_sell_kzt_to_rub = await get_fiat_exchange_rate(get_sell_usdt_to_rub * buy, get_sell_kzt_to_usdt, getrate)
    get_sell_kzt_to_uyu = await get_fiat_exchange_rate(get_sell_usdt_to_uyu * buy, get_sell_kzt_to_usdt, getrate)
    get_sell_rub_to_kzt = await get_fiat_exchange_rate(get_sell_usdt_to_kzt * buy, get_sell_rub_to_usdt, getrate)
    get_sell_uyu_to_kzt = await get_fiat_exchange_rate(get_sell_usdt_to_kzt * buy, get_sell_uyu_to_usdt, getrate)
    get_sell_rub_to_uyu = await get_fiat_exchange_rate(get_sell_usdt_to_uyu * buy, get_sell_rub_to_usdt, getrate)
    get_sell_uyu_to_rub = await get_fiat_exchange_rate(get_sell_usdt_to_rub * buy, get_sell_uyu_to_usdt, getrate)
    # get_sell_usdt_to_ma = process_binance(commission=False, action="SELL", fiat="MAD", bank=["CIHBank"])
    # get_sell_mad_to_usd = process_binance(commission=False, action="BUY", fiat="MAD", bank=["CIHBank"])
    # get_sell_usdt_to_ru = process_kucoin(commission=False, action='BUY', fiat='RUB', bank="SBP")
    # get_sell_rub_to_usd = process_kucoin(commission=False, action='SELL', fiat='RUB', bank="SBP")
    # get_sell_usdt_to_kz = process_binance(commission=False, action="SELL", fiat="KZT", bank=["KaspiBank"])
    # get_sell_kzt_to_usd = process_binance(commission=False, action="BUY", fiat="KZT", bank=["KaspiBank"])
    # get_sell_usdt_to_uy = process_binance(commission=False, action="SELL", fiat="UYU", bank=["Prex"])
    # get_sell_uyu_to_usd = process_binance(commission=False, action="BUY", fiat="UYU", bank=["Prex"])
    # get_sell_mad_to_ru = get_fiat_exchange_rate(get_sell_usdt_to_ru, get_sell_mad_to_usd, getrate)
    # get_sell_mad_to_kz = get_fiat_exchange_rate(get_sell_usdt_to_kz, get_sell_mad_to_usd, getrate)
    # get_sell_mad_to_uy = get_fiat_exchange_rate(get_sell_usdt_to_uy, get_sell_mad_to_usd, getrate)
    # get_sell_rub_to_ma = get_fiat_exchange_rate(get_sell_usdt_to_ma, get_sell_rub_to_usd, getrate)
    # get_sell_kzt_to_ma = get_fiat_exchange_rate(get_sell_usdt_to_ma, get_sell_kzt_to_usd, getrate)
    # get_sell_uyu_to_ma = get_fiat_exchange_rate(get_sell_usdt_to_ma, get_sell_uyu_to_usd, getrate)
    # get_sell_kzt_to_ru = get_fiat_exchange_rate(get_sell_usdt_to_ru, get_sell_kzt_to_usd, getrate)
    # get_sell_kzt_to_uy = get_fiat_exchange_rate(get_sell_usdt_to_uy, get_sell_kzt_to_usd, getrate)
    # get_sell_rub_to_kz = get_fiat_exchange_rate(get_sell_usdt_to_kz, get_sell_rub_to_usd, getrate)
    # get_sell_uyu_to_kz = get_fiat_exchange_rate(get_sell_usdt_to_kz, get_sell_uyu_to_usd, getrate)
    # get_sell_rub_to_uy = get_fiat_exchange_rate(get_sell_usdt_to_uy, get_sell_rub_to_usd, getrate)
    # get_sell_uyu_to_ru = get_fiat_exchange_rate(get_sell_usdt_to_ru, get_sell_uyu_to_usd, getrate)
    d = {
        'get_sell_usdt_to_mad': get_sell_usdt_to_mad,
        'get_sell_mad_to_usdt': get_sell_mad_to_usdt,
        'get_sell_usdt_to_rub': get_sell_usdt_to_rub,
        'get_sell_rub_to_usdt': get_sell_rub_to_usdt,
        'get_sell_usdt_to_kzt': get_sell_usdt_to_kzt,
        'get_sell_kzt_to_usdt': get_sell_kzt_to_usdt,
        'get_sell_usdt_to_uyu': get_sell_usdt_to_uyu,
        'get_sell_uyu_to_usdt': get_sell_uyu_to_usdt,
        'get_sell_mad_to_rub': get_sell_mad_to_rub,
        'get_sell_mad_to_kzt': get_sell_mad_to_kzt,
        'get_sell_mad_to_uyu': get_sell_mad_to_uyu,
        'get_sell_rub_to_mad': get_sell_rub_to_mad,
        'get_sell_kzt_to_mad': get_sell_kzt_to_mad,
        'get_sell_uyu_to_mad': get_sell_uyu_to_mad,
        'get_sell_kzt_to_rub': get_sell_kzt_to_rub,
        'get_sell_kzt_to_uyu': get_sell_kzt_to_uyu,
        'get_sell_rub_to_kzt': get_sell_rub_to_kzt,
        'get_sell_uyu_to_kzt': get_sell_uyu_to_kzt,
        'get_sell_rub_to_uyu': get_sell_rub_to_uyu,
        'get_sell_uyu_to_rub': get_sell_uyu_to_rub,
    }
    key = cache_key(t, commission, getrate)
    print(key)
    await async_cache.set(key, d)
    return d


@bot.message_handler(commands=['get_rates', '77'])
async def send_rates(message):

    t = message.text
    try:
        fresh_rates = await get_final_exchange_rate(t)
    except IndexError as e:
        logging.error(f'сломались ссылки {e}', exc_info=True)

    await bot.send_message(message.from_user.id, f"""Курсы валют (средние цены продажи)
относительно предложения по рынкам

система:
- (продаю) за (получаю)   (количество которое получу за 1 у.е. или заплачу за 1 у.е. получаемой валюты)
                        USDT:
- USDT за MAD       {round(fresh_rates['get_sell_usdt_to_mad'], 3)} MAD
- MAD за USDT       {round(fresh_rates['get_sell_mad_to_usdt'], 3)} MAD
- USDT за RUB        {round(fresh_rates['get_sell_usdt_to_rub'], 3)} RUB
- RUB за USDT        {round(fresh_rates['get_sell_rub_to_usdt'], 3)} RUB
- USDT за KZT        {round(fresh_rates['get_sell_usdt_to_kzt'], 3)} KZT
- KZT за USDT        {round(fresh_rates['get_sell_kzt_to_usdt'], 3)} KZT
- USDT за UYU        {round(fresh_rates['get_sell_usdt_to_uyu'], 3)} UYU
- UYU за USDT        {round(fresh_rates['get_sell_uyu_to_usdt'], 3)} UYU

                        MAD:
- MAD за RUB        {round(fresh_rates['get_sell_mad_to_rub'], 3)} RUB
- MAD за KZT         {round(fresh_rates['get_sell_mad_to_kzt'], 3)} KZT
- MAD за UYU         {round(fresh_rates['get_sell_mad_to_uyu'], 3)} UYU
- RUB за MAD        {round(fresh_rates['get_sell_rub_to_mad'], 3)} RUB
- KZT за MAD        {round(fresh_rates['get_sell_kzt_to_mad'], 3)} KZT
- UYU за MAD        {round(fresh_rates['get_sell_uyu_to_mad'], 3)} UYU

                        RUB:
- RUB за MAD        {round(fresh_rates['get_sell_rub_to_mad'], 3)} RUB
- RUB за KZT         {round(fresh_rates['get_sell_rub_to_kzt'], 3)} KZT
- RUB за UYU         {round(fresh_rates['get_sell_rub_to_uyu'], 3)} UYU
- MAD за RUB        {round(fresh_rates['get_sell_mad_to_rub'], 3)} RUB
- KZT за RUB         {round(fresh_rates['get_sell_kzt_to_rub'], 3)} KZT
- UYU за RUB         {round(fresh_rates['get_sell_uyu_to_rub'], 3)} RUB

                        KZT:
- KZT за MAD        {round(fresh_rates['get_sell_kzt_to_mad'], 2)} KZT
- KZT за RUB         {round(fresh_rates['get_sell_kzt_to_rub'], 2)} KZT
- KZT за UYU         {round(fresh_rates['get_sell_kzt_to_uyu'], 2)} KZT
- MAD за KZT         {round(fresh_rates['get_sell_mad_to_kzt'], 2)} KZT
- RUB за KZT         {round(fresh_rates['get_sell_rub_to_kzt'], 2)} KZT
- UYU за KZT         {round(fresh_rates['get_sell_uyu_to_kzt'], 2)} KZT

                        UYU:
- UYU за MAD        {round(fresh_rates['get_sell_uyu_to_mad'], 3)} UYU
- UYU за KZT         {round(fresh_rates['get_sell_uyu_to_kzt'], 3)} KZT
- UYU за RUB         {round(fresh_rates['get_sell_uyu_to_rub'], 3)} RUB
- MAD за UYU         {round(fresh_rates['get_sell_mad_to_uyu'], 3)} UYU
- KZT за UYU         {round(fresh_rates['get_sell_kzt_to_uyu'], 3)} RUB
- RUB за UYU         {round(fresh_rates['get_sell_rub_to_uyu'], 3)} KZT

Напишите нам, чтобы узнать стоимость с учётом комиссии.
@SudokuH
""")


@bot.message_handler(commands=['rates'])
async def send_current_message(message):
    t = message.text
    try:
        fresh_rates = await get_final_exchange_rate(t=None, commission=True, getrate=True)
    except IndexError as e:
        logging.error(f'сломались ссылки {e}', exc_info=True)
    # Ваш код для отправки сообщения
    # print(message.chat.id)
    chat = group_chat_id
    # pprint(str(message.chat))
    await bot.send_message(message.chat.id, "С помощью меня можно узнать актуальные курсы обмена.\n"
                                            "Наши курсы с комиссией:\n"
                                            f"- MAD за RUB {round(fresh_rates['get_sell_mad_to_rub'], 3)} RUB\n"
    # f"- MAD за KZT         {round(fresh_rates['get_sell_mad_to_kzt'], 3)} KZT"
    # f"- MAD за UYU         {round(fresh_rates['get_sell_mad_to_uyu'], 3)} UYU"
                                            f"- RUB за MAD {round(fresh_rates['get_sell_rub_to_mad'], 3)} RUB\n"
    # f"- KZT за MAD        {round(fresh_rates['get_sell_kzt_to_mad'], 3)} KZT"
    # f"- UYU за MAD        {round(fresh_rates['get_sell_uyu_to_mad'], 3)} UYU"
                                            f"@SudokuH")
    # if message.chat.id == message.from_user.id:
    #     await bot.send_message(message.from_user.id, "С помощью меня можно узнать актуальные курсы обмена.\n"
    #                                                  "Наши курсы с комиссией:\n"
    #                                                  f"- MAD за RUB {round(fresh_rates['get_sell_mad_to_rub'], 3)} RUB\n"
    #                                                  f"- RUB за MAD {round(fresh_rates['get_sell_rub_to_mad'], 3)} RUB\n"
    #                                                  f"@SudokuH")


async def process_kucoin(commission, action, fiat, bank):
    url = 'https://www.kucoin.com/_api/otc/ad/list?status=PUTUP&currency=' \
          f'USDT&legal={fiat}&page=1&pageSize=10&side={action}&amount=&payTypeCodes={bank}&lang=ru_RU'
    headers = {
        'accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                      ' (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
    }

    response = requests.get(url=url, headers=headers).json()
    prices = []
    if not response["items"]:
        return 1
    for i in range(10):
        price = response["items"][i]['floatPrice']
        prices.append(float(price))
    avg_price = sum(prices) / len(prices)
    if commission:
        if action == 'BUY':
            avg_price = avg_price * 0.9925
        else:
            avg_price = avg_price * 1.0075
    return avg_price


async def process_binance(commission, action, fiat, bank):
    url = 'https://c2c.binance.com/bapi/c2c/v2/friendly/c2c/adv/search'
    headers = {
        'accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                      ' (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
    }
    payload = {"fiat": fiat,
               "page": 1,
               "rows": 10,
               "tradeType": action,
               "asset": "USDT",
               "countries": [],
               "proMerchantAds": False,
               "shieldMerchantAds": False,
               "publisherType": None,
               "payTypes": bank,
               "classifies": ["mass", "profession"]}
    response = requests.post(url=url, headers=headers, json=payload).json()
    # pprint(response)
    prices = []
    much_offers = len(response['data'])
    if not response['data']:
        return 1
    quantity = range(10) if much_offers >= 10 else range(much_offers)
    for i in quantity:
        price = response['data'][i]['adv']['price']
        prices.append(float(price))
    if sum(prices) and len(prices):
        avg_price = sum(prices) / len(prices)
    else:
        avg_price = 0
    if commission:
        if action == 'SELL':
            avg_price = avg_price * 0.9925
        else:
            avg_price = avg_price * 1.0075
    return avg_price


# import re
# wrong_words = 'Связка, Профит'

# @bot.message_handler(regexp=wrong_words)
# async def watcher(message):
#     text: str = message.text
#     print(re.split('[; |, |\*|\n|. ]', text))
#     septed_text = re.split('[; |, |\*|\n|. ]', text)
#
#     for w in wrong_words:
#         if w in septed_text:
#             await bot.delete_message(message.chat.id, message.id)
#             await bot.ban_chat_member(message.chat.id, message.from_user.id, 1)
#             logging.info('DELETE USER -'
#                          f'{message.from_user.id, message.from_user.username if message.from_user.id else None}')


if __name__ == '__main__':
    try:
        # subprocess.Popen(["venv\Scripts\python.exe", "schedule_task.py"])
        asyncio.run(bot.polling(none_stop=True))
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        print("Restarting the script in 10 seconds...")
        time.sleep(10)  # Подождите 10 секунд перед перезапуском
        bot.send_message(5170994439, f"{e, traceback.format_exc()},")
# + кеш,
# + комиссии в калькулятор
# + допустимо написать гет рэйтс -1 USDT за 10.594 MAD или только фиаты так написать
# + удалёнка
# + env













