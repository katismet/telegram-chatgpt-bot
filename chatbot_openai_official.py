import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Попытка загрузить переменные из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Для загрузки .env файла установите python-dotenv: pip install python-dotenv")

# Настройка подробного логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Получение токенов из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Проверка наличия токенов
if not TELEGRAM_TOKEN:
    raise ValueError("Не установлена переменная окружения TELEGRAM_TOKEN")
if not OPENAI_API_KEY:
    raise ValueError("Не установлена переменная окружения OPENAI_API_KEY")

# Инициализация OpenAI клиента с ОФИЦИАЛЬНЫМ API
client = OpenAI(
    api_key=OPENAI_API_KEY,
    # Используем официальный OpenAI API endpoint
    # base_url="https://api.openai.com/v1"  # По умолчанию
)

# Системное сообщение для GPT-5 Nano
SYSTEM_MESSAGE = """Ты вежливый и профессиональный личный помощник-секретарь, работающий в Telegram. 

Твои качества:
- Всегда вежлив и дружелюбен
- Отвечаешь кратко, но информативно
- Используешь эмодзи для лучшего восприятия
- Помогаешь с различными задачами
- Общаешься на русском языке

Ты можешь помочь с:
- Ответами на вопросы
- Планированием и организацией
- Поиском информации
- Решением задач
- И многим другим!

Будь полезным и дружелюбным помощником! 😊"""

def log_message(direction: str, user_name: str, user_id: int, message: str, message_type: str = "text"):
    """Логирует входящие и исходящие сообщения"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    direction_icon = "📥" if direction == "IN" else "📤"
    type_icon = "💬" if message_type == "text" else "⚡"
    
    # Обрезаем длинные сообщения для удобства чтения
    if len(message) > 100:
        display_message = message[:97] + "..."
    else:
        display_message = message
    
    print(f"{timestamp} {direction_icon} {type_icon} [{direction}] {user_name} (ID: {user_id}): {display_message}")

async def get_chatgpt_response(user_message: str) -> str:
    """
    Отправляет сообщение пользователя в OpenAI ChatGPT и возвращает ответ
    
    Args:
        user_message (str): Сообщение пользователя
        
    Returns:
        str: Ответ от ChatGPT
    """
    try:
        print(f"🤖 [AI] Отправка запроса к OpenAI (GPT-5 Nano)...")
        response = client.chat.completions.create(
            model="gpt-5-nano",  # Используем новейшую модель GPT-5 Nano
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_message}
            ]
        )
        
        ai_response = response.choices[0].message.content
        print(f"🤖 [AI] Получен ответ от OpenAI ({len(ai_response)} символов)")
        return ai_response
        
    except Exception as e:
        error_msg = f"Ошибка при обращении к OpenAI: {e}"
        logger.error(error_msg)
        print(f"❌ [ERROR] {error_msg}")
        return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    log_message("IN", user.first_name, user.id, "/start", "command")
    
    welcome_message = (
        "Привет! 👋 Я ваш персональный помощник-секретарь на базе GPT-5 Nano! 🧠\n\n"
        "Я готов помочь вам с любыми вопросами и задачами. "
        "Просто напишите мне сообщение, и я постараюсь быть максимально полезным!\n\n"
        "💡 Используйте /help для получения справки.\n"
        "🚀 Начните общение прямо сейчас!"
    )
    
    await update.message.reply_text(welcome_message)
    log_message("OUT", user.first_name, user.id, welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    user = update.effective_user
    log_message("IN", user.first_name, user.id, "/help", "command")
    
    help_text = (
        "🤖 **Доступные команды:**\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "🧠 **О боте:**\n"
        "Я работаю на базе новейшей модели GPT-5 Nano от OpenAI!\n\n"
        "💡 **Как использовать:**\n"
        "Просто отправьте мне любое текстовое сообщение, и я отвечу вам как ваш личный помощник.\n\n"
        "✨ **Я могу помочь с:**\n"
        "• Ответами на вопросы\n"
        "• Планированием задач\n"
        "• Поиском информации\n"
        "• Решением проблем\n"
        "• Творческими задачами\n"
        "• И многим другим!\n\n"
        "🚀 Начните общение прямо сейчас!"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')
    log_message("OUT", user.first_name, user.id, help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user = update.effective_user
    user_message = update.message.text
    
    # Логируем входящее сообщение
    log_message("IN", user.first_name, user.id, user_message)
    
    # Отправляем индикатор набора текста
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    print(f"⌨️ [TYPING] Показываем индикатор набора текста для {user.first_name}")
    
    # Получаем ответ от ChatGPT
    response = await get_chatgpt_response(user_message)
    
    # Отправляем ответ пользователю
    await update.message.reply_text(response)
    
    # Логируем исходящее сообщение
    log_message("OUT", user.first_name, user.id, response)

async def handle_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нетекстовых сообщений"""
    user = update.effective_user
    message_type = update.message.content_type
    
    log_message("IN", user.first_name, user.id, f"[{message_type.upper()}]", message_type)
    
    response = (
        "Извините, я обрабатываю только текстовые сообщения. "
        "Пожалуйста, отправьте текстовое сообщение."
    )
    
    await update.message.reply_text(response)
    log_message("OUT", user.first_name, user.id, response)

def main() -> None:
    """Основная функция запуска бота"""
    print("=" * 60)
    print("🤖 ЗАПУСК TELEGRAM БОТА С GPT-5 NANO")
    print("=" * 60)
    print(f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"🔑 Telegram Token: {TELEGRAM_TOKEN[:20]}...")
    print(f"🔑 OpenAI API Key: {OPENAI_API_KEY[:20]}...")
    print("🌐 API Endpoint: https://api.openai.com/v1")
    print("🧠 AI Model: GPT-5 Nano (новейшая модель)")
    print("=" * 60)
    print("📥 Входящие сообщения помечены как [IN]")
    print("📤 Исходящие сообщения помечены как [OUT]")
    print("=" * 60)
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(~filters.TEXT, handle_non_text))

    # Запускаем бота
    print("🚀 Бот запущен и ожидает сообщения...")
    print("=" * 60)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
