import logging
import os
import requests
import sys
import time

from telegram import Bot

from dotenv import load_dotenv


load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}

bot = Bot(token=TELEGRAM_TOKEN)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s || %(levelname)s || %(name)s || %(message)s'
)
logger = logging.getLogger('logfile')
logger.addHandler(logging.FileHandler('logfile'))
logger.addHandler(logging.StreamHandler(sys.stdout))


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework_name is None:
        homework_name = 'UNKNOWN'
    if homework.get('status') is None:
        verdict = 'UNKNOWN'
    elif homework.get('status') == 'rejected':
        verdict = 'К сожалению, в работе нашлись ошибки.'
    elif homework.get('status') == 'reviewing':
        verdict = 'Работа взята в ревью'
    else:
        verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(URL, headers=HEADERS, params=payload)
        return homework_statuses.json()
    except requests.exceptions.RequestException as e:
        raise e


def send_message(message):
    logger.info('Сообщение отправлено.')
    return bot.send_message(chat_id=CHAT_ID, text=message)


def main():
    logger.debug('Бот запущен.')
    current_timestamp = int(time.time())

    while True:
        try:
            homeworks = get_homeworks(current_timestamp)
            if type(homeworks) == requests.exceptions.RequestException:
                logger.error(homeworks, exc_info=True)
                send_message("Не удалось получить данные от Яндекса")
            else:
                current_timestamp = homeworks.get('current_date')
                if len(homeworks.get('homeworks')) > 0:
                    last_homework = homeworks.get('homeworks')[0]
                    text_message = parse_homework_status(last_homework)
                    send_message(text_message)
            time.sleep(5 * 60)
        except Exception as e:
            logger.error(e, exc_info=True)
            logger.info('Сообщение отправлено')
            send_message(f'Бот упал с ошибкой: {e}')
            print(f'Бот упал с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
