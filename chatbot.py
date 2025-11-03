import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
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

# Инициализация OpenAI клиента
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)

# Системное сообщение для ChatGPT
SYSTEM_MESSAGE = "Ты вежливый и профессиональный личный помощник, работающий в Telegram."

async def get_chatgpt_response(user_message: str) -> str:
    """
    Отправляет сообщение пользователя в OpenAI ChatGPT и возвращает ответ
    
    Args:
        user_message (str): Сообщение пользователя
        
    Returns:
        str: Ответ от ChatGPT
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Ошибка при обращении к OpenAI: {e}")
        return "Извините, произошла ошибка при обработке вашего запроса. Попробуйте позже."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    welcome_message = (
        "Привет! 👋 Я ваш персональный помощник-секретарь.\n\n"
        "Я готов помочь вам с любыми вопросами и задачами. "
        "Просто напишите мне сообщение, и я постараюсь быть полезным!\n\n"
        "Используйте /help для получения справки."
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "🤖 **Доступные команды:**\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "💡 **Как использовать:**\n"
        "Просто отправьте мне любое текстовое сообщение, и я отвечу вам как ваш личный помощник.\n\n"
        "Я могу помочь с:\n"
        "• Ответами на вопросы\n"
        "• Планированием задач\n"
        "• Поиском информации\n"
        "• И многим другим!"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    user_name = update.effective_user.first_name
    
    # Отправляем индикатор набора текста
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    # Получаем ответ от ChatGPT
    response = await get_chatgpt_response(user_message)
    
    # Отправляем ответ пользователю
    await update.message.reply_text(response)

async def handle_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нетекстовых сообщений"""
    await update.message.reply_text(
        "Извините, я обрабатываю только текстовые сообщения. "
        "Пожалуйста, отправьте текстовое сообщение."
    )

def main() -> None:
    """Основная функция запуска бота"""
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(~filters.TEXT, handle_non_text))

    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
