import logging
import os
import sys

import requests
from telebot import TeleBot
from dotenv import load_dotenv

from exceptions import ProtocolError

load_dotenv()

WEATHER_TOKEN = os.getenv('WEATHER_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

ENDPOINT = 'https://api.openweathermap.org/data/2.5/find'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = [WEATHER_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    missing_tokens = []
    for token in tokens:
        if not token:
            missing_tokens.append(token)
    if missing_tokens:
        error_message = f'Нет переменной окружения {missing_tokens}'
        logging.critical(error_message)
        raise SystemExit(error_message)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logging.info('Отправляется сообщение')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Сообщение отправлено')
    except Exception as error:
        logging.error(f'Сообщение не отправлено: {error}')


def get_weather(city):
    """Делает запрос к эндпоинту API-сервиса."""
    params = {
        'q': city,
        'units': 'metric',
        'lang': 'ru',
        'appid': WEATHER_TOKEN,
    }
    try:
        response = requests.get(ENDPOINT, params=params)
        if response.status_code != 200:
            raise ProtocolError(
                f'Ошибка при получении погоды для {city}: {response.status_code}')
        data = response.json()
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        description = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind_speed = data['wind']['speed']
        weather_info = (
            f'Погода в городе {city}:\n'
            f'Температура: {temp}°C\n'
            f'Ощущается как: {feels_like}°C\n'
            f'Описание: {description.capitalize()}\n'
            f'Влажность: {humidity}%\n'
            f'Скорость ветра: {wind_speed} м/с'
        )
        return weather_info
    except requests.exceptions.RequestException as error:
        raise ConnectionError(
            f'Сбой в работе: Во время подключения к эндпоинту {ENDPOINT}'
            f'произошла непредвиденная ошибка: {error}.'
        )


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        welcome_text = (
            "Добро пожаловать! Используйте /weather <город> для получения текущей погоды."
        )
        send_message(bot, message.chat.id, welcome_text)

    @bot.message_handler(commands=['weather'])
    def handle_weather(message):
        try:
            args = message.text.strip().split(maxsplit=1)
            if len(args) < 2 or not args[1]:
                send_message(
                    bot, message.chat.id, 'Пожалуйста, укажите город. Использование: /weather <город>')
                return

            city = args[1]

            weather_info = get_weather(city)
            send_message(bot, message.chat.id, weather_info)
        except Exception as e:
            send_message(bot, message.chat.id, f'Произошла ошибка: {e}')
            logging.error(f'Ошибка при обработке запроса погоды: {e}')

    @bot.message_handler(func=lambda message: True)
    def echo_all(message):
        send_message(bot, message.chat.id,
                     'Неизвестная команда. Используйте /help для справки.')

    logging.info('Бот запущен и готов к работе.')
    bot.polling(none_stop=True)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        filename='homework_log.log',
        handler=logging.StreamHandler(stream=sys.stdout),
        format='%(asctime)s, %(levelname)s, %(funcName)s, %(message)s',
    )
    main()
