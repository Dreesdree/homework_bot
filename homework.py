import telegram
import os
import time
import logging
import requests
import exceptions

from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('P_TOKEN')
TELEGRAM_TOKEN = os.getenv('T_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('T_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream='sys.stdout')


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.info('Сообщение отправлено')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception:
        message_error = 'Сбой при отправки сообщения'
        logging.error(message_error)
        raise exceptions.SendMessageException(message_error)


def get_api_answer(current_timestamp):
    """Отправляет запрос к эндпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        message_error = 'Недоступен эндпоинт'
        logging.error(message_error)
        raise exceptions.GetAPIException(message_error)
    if response.status_code != HTTPStatus.OK:
        response.raise_for_status()
        message_error = 'Сбой в работе, неверный статус ответ'
        logger.error(message_error)
        raise exceptions.GetAPIException(message_error)
    return response.json()


def check_response(response):
    """Проверяет корректность ответа API."""
    try:
        homework = response['homeworks']
    except KeyError:
        message_error = 'Отсутствие ожидаемых ключей'
        logging.error(message_error)
        raise KeyError(message_error)
    if not homework:
        message_error = 'Пустой список'
        logging.error(message_error)
        raise exceptions.CheckResponseException(message_error)
    if not isinstance(homework, list):
        message_error = 'Неверный тип данных'
        logging.error(message_error)
        raise TypeError(message_error)
    return homework


def parse_status(homework):
    """Извлекает конкретную информацию из запроса."""
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    except KeyError:
        message_error = 'Отстувуют ключи'
        logging.error(message_error)
        raise KeyError(message_error)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            check_response(response)
            if not check_tokens():
                logger.critical('Отсутствует переменная окружения!')
                raise SystemExit()
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.exception(f'Появилась ошибка: {error}')
            send_message(f'{message} {error}', bot)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
