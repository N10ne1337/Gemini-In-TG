import os
import configparser
import requests  # Для запросов к Gemini API
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Функция для загрузки или запроса API-ключей
def load_or_request_api_keys():
    config = configparser.ConfigParser()
    config_file = 'config.ini'

    if not os.path.exists(config_file):
        print("Привет! Это первый запуск. Пожалуйста, введи свои API-ключи.")
        gemini_api_key = input("Введи API-ключ от Gemini: ")
        telegram_api_key = input("Введи API-ключ от Telegram бота: ")

        config['API_KEYS'] = {
            'gemini_api_key': gemini_api_key,
            'telegram_api_key': telegram_api_key
        }

        with open(config_file, 'w') as configfile:
            config.write(configfile)
        print("Спасибо! Ключи сохранены в config.ini.")
    else:
        config.read(config_file)
        gemini_api_key = config['API_KEYS']['gemini_api_key']
        telegram_api_key = config['API_KEYS']['telegram_api_key']

    return gemini_api_key, telegram_api_key

# Функция для взаимодействия с Gemini API
def ask_gemini(api_key, prompt):
    url = "https://api.gemini.com/v1/chat"  # Пример URL, уточни у документации Gemini
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "max_tokens": 150  # Пример параметра, настрой под свои нужды
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get("response", "Не удалось получить ответ от Gemini.")
    else:
        return f"Ошибка: {response.status_code}"

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот, готовый к диалогу. Напиши что-нибудь!")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    gemini_api_key = context.bot_data.get('gemini_api_key')

    # Отправляем запрос в Gemini
    gemini_response = ask_gemini(gemini_api_key, user_message)

    # Отправляем ответ пользователю
    await update.message.reply_text(gemini_response)

# Основная функция
def main():
    # Загружаем или запрашиваем API-ключи
    gemini_api_key, telegram_api_key = load_or_request_api_keys()

    # Создаем приложение для Telegram бота
    application = Application.builder().token(telegram_api_key).build()

    # Сохраняем API-ключ Gemini в данных бота
    application.bot_data['gemini_api_key'] = gemini_api_key

    # Регистрируем обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
