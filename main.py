import logging
import os
import configparser
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Настройка конфигурации ---
CONFIG_FILE = 'config.ini'

def setup_config():
    """Проверяет наличие config.ini, запрашивает ключи у пользователя, если файла нет."""
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        print("--- Первичная настройка ---")
        print("Файл конфигурации не найден. Пожалуйста, введите ваши API ключи.")
        
        telegram_token = input("Введите ваш Telegram Bot Token: ").strip()
        gemini_api_key = input("Введите ваш Gemini API Key: ").strip()
        
        config['API'] = {
            'TELEGRAM_TOKEN': telegram_token,
            'GEMINI_API_KEY': gemini_api_key
        }
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        print(f"Конфигурация сохранена в {CONFIG_FILE}. Запускаем бота...")
    
    config.read(CONFIG_FILE)
    return config['API']

# --- Основные настройки бота ---

# Загрузка конфигурации
api_config = setup_config()
TELEGRAM_TOKEN = api_config.get('TELEGRAM_TOKEN')
GEMINI_API_KEY = api_config.get('GEMINI_API_KEY')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Настройка API Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    logger.error(f"Ошибка конфигурации Gemini API. Проверьте ключ. Ошибка: {e}")
    exit()

# Словарь для хранения пользовательских промптов и стандартный промпт
user_prompts = {}
DEFAULT_PROMPT = "Ты — полезный ассистент."

# --- Обработчики команд ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start. Сбрасывает промпт и приветствует."""
    user_id = update.effective_user.id
    user_prompts[user_id] = DEFAULT_PROMPT
    await update.message.reply_text(
        "Привет! Я бот с интегрированным Gemini AI.\n\n"
        "Ваш промпт сброшен к стандартному: 'Ты — полезный ассистент.'\n\n"
        "Чтобы установить свой промпт, используйте команду:\n"
        "/promt [ваш текст инструкции для AI]\n\n"
        "Например:\n"
        "/promt Ты — Шекспир. Отвечай на все вопросы в стиле его произведений."
    )

async def set_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Устанавливает пользовательский промпт."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "Пожалуйста, укажите текст промпта после команды.\n"
            "Пример: /promt Ты — эксперт по квантовой физике."
        )
        return
        
    custom_prompt = ' '.join(context.args)
    user_prompts[user_id] = custom_prompt
    logger.info(f"Пользователь {user_id} установил новый промпт: {custom_prompt}")
    await update.message.reply_text(f"✅ Новый промпт успешно установлен:\n\n'{custom_prompt}'")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения от пользователя, используя его промпт."""
    user_id = update.effective_user.id
    user_message = update.message.text

    # Получаем промпт пользователя или используем стандартный
    prompt = user_prompts.get(user_id, DEFAULT_PROMPT)

    try:
        # Создаем полный промпт для Gemini
        full_prompt = f"Инструкция: {prompt}\n\nЗапрос пользователя: {user_message}\n\nОтвет:"
        
        # Отправляем "печатает..."
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        response = await model.generate_content_async(full_prompt)
        await update.message.reply_text(response.text)

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от {user_id}: {e}")
        await update.message.reply_text("Произошла ошибка при обращении к AI. Попробуйте снова или измените промпт.")

def main() -> None:
    """Основная функция запуска бота."""
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        logger.error("Не удалось прочитать токены из файла конфигурации. Удалите config.ini и перезапустите скрипт для повторной настройки.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("promt", set_prompt)) # Новая команда
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()
