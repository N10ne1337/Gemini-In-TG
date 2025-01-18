import os
import configparser
import google.generativeai as genai
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

# Функция для инициализации Gemini API
def initialize_gemini(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот, использующий Gemini API. Напиши что-нибудь!")

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    gemini_model = context.bot_data.get('gemini_model')

    # Отправляем запрос в Gemini
    try:
        response = gemini_model.generate_content(user_message)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")

# Основная функция
def main():
    # Загружаем или запрашиваем API-ключи
    gemini_api_key, telegram_api_key = load_or_request_api_keys()

    # Инициализируем Gemini API
    gemini_model = initialize_gemini(gemini_api_key)

    # Создаем приложение для Telegram бота
    application = Application.builder().token(telegram_api_key).build()

    # Сохраняем модель Gemini в данных бота
    application.bot_data['gemini_model'] = gemini_model

    # Регистрируем обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
