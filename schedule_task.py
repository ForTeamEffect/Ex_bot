import schedule
import time
import asyncio
import os
import re
import logging

from telebot import TeleBot  # Импортируйте вашу библиотеку для работы с Telegram
from main import get_final_exchange_rate

# Ваш бот
key_bot = os.getenv('EXCHANGE_BOT')
group_chat_id = os.getenv('EXCHANGE_CHAT')
bot = TeleBot(key_bot)
logging.basicConfig(filename='bot_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='UTF-8')

# group_chat_id = -1001718604663
# Функция для отправки ежедневного сообщения
# def send_daily_message():
#     fresh_rates = asyncio.run(get_final_exchange_rate(t=None, commission=True, getrate=True))
#     # Ваш код для отправки сообщения
#     bot.send_message(group_chat_id, "С помощью меня можно узнать актуальные курсы обмена.\n"
#                                     "Наши курсы с комиссией:\n"
#                                     f"- MAD за RUB {round(fresh_rates['get_sell_mad_to_rub'], 3)} RUB\n"
#                                     # f"- MAD за KZT         {round(fresh_rates['get_sell_mad_to_kzt'], 3)} KZT"
#                                     # f"- MAD за UYU         {round(fresh_rates['get_sell_mad_to_uyu'], 3)} UYU"
#                                     f"- RUB за MAD {round(fresh_rates['get_sell_rub_to_mad'], 3)} RUB\n"
#                                     # f"- KZT за MAD        {round(fresh_rates['get_sell_kzt_to_mad'], 3)} KZT"
#                                     # f"- UYU за MAD        {round(fresh_rates['get_sell_uyu_to_mad'], 3)} UYU"
#                                     f"@SudokuH")
#
#
# # Расписание для выполнения функции каждый день в определенное время
# schedule.every().day.at("18:34").do(send_daily_message)

@bot.message_handler()
async def watcher(message):
    text: str = message.text
    print(re.split('[; |, |\*|\n|. ]', text))
    septed_text = re.split('[; |, |\*|\n|. ]', text)
    wrong_words = ['связка', 'профит', 'бесплатное', 'обучение', 'доход', 'обучаться',
                   '18+', 'прибыльные', 'прибыль', 'прибыльное', 'прибыльно', 'заработка',
                   'удалённую', 'удaлённой', 'удaлённо', 'работы', 'работа', 'Работать', ]
    for w in wrong_words:
        if w.lower() in septed_text:
            bot.delete_message(message.chat.id, message.id)
            bot.ban_chat_member(message.chat.id, message.from_user.id, 1)
            logging.info('DELETE USER -'
                         f'{message.from_user.id, message.from_user.username if message.from_user.id else None}')
# Асинхронный цикл для выполнения расписания
# def job():
#     while True:
#         # schedule.run_pending()
#         time.sleep(10)


if __name__ == "__main__":
    try:
        bot.polling(non_stop=True)
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Restarting the script in 10 seconds...")
        time.sleep(10)  # Подождите 10 секунд перед перезапуском
