import telegram
import os
import time
import logging
import requests
import exceptions

from typing import Dict
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


def init_logger() -> object:
    """Настройки логгера."""
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        format='%(asctime)s, %(levelname)s, %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream='sys.stdout')
    return logger


logger = init_logger()


def send_message(bot: None, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.info('Сообщение отправлено')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception:
        message_error = 'Сбой при отправки сообщения'
        logging.error(message_error)


def get_api_answer(current_timestamp: Dict[str, str]) -> dict:
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
    try:
        return response.json()
    except ValueError:
        message_error = 'Ответ не в формате json'
        logging.error(message_error)
        raise exceptions.GetAPIException(message_error)


def check_response(response: Dict[str, str]) -> dict:
    """Проверяет корректность ответа API."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        message_error = 'Отсутствие ожидаемых ключей'
        logging.error(message_error)
        raise KeyError(message_error)
    if not isinstance(homeworks, list):
        message_error = 'Неверный тип данных'
        logging.error(message_error)
        raise TypeError(message_error)
    if not homeworks:
        message_error = 'Пустой список'
        logging.error(message_error)
        raise exceptions.CheckResponseException(message_error)
    return homeworks


def parse_status(homework: Dict[str, str]) -> str:
    """Извлекает конкретную информацию из запроса."""
    try:
        homework_name = homework['homework_name']
    except KeyError as error:
        error_message = f'В словаре нет ключа homework_name {error}'
        logger.error(error_message)
        raise KeyError(error_message)
    try:
        homework_status = homework['status']
    except KeyError as error:
        error_message = f'В словаре нет ключа status {error}'
        logger.error(error_message)
        raise KeyError(error_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> None:
    """Проверка токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        message_error = 'Отсутствует переменная окружения!'
        logger.critical(message_error)
        raise SystemExit(message_error)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            message = parse_status(homeworks[0])
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.exception(f'Появилась ошибка: {error}')
            send_message(bot, f'{message} {error}')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
