# Быстрый запуск Telegram-бота

## 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

## 2. Настройка токенов

### Вариант A: Переменные окружения
```bash
# Windows
set TELEGRAM_TOKEN=your_telegram_token
set OPENAI_API_KEY=your_openai_key

# Linux/Mac
export TELEGRAM_TOKEN=your_telegram_token
export OPENAI_API_KEY=your_openai_key
```

### Вариант B: .env файл
1. Создайте файл `.env` в корне проекта
2. Добавьте в него:
```
TELEGRAM_TOKEN=your_telegram_token
OPENAI_API_KEY=your_openai_key
```

## 3. Тестирование подключения
```bash
python test_openai.py
```

## 4. Запуск бота
```bash
# Основная версия
python chatbot.py

# Или с поддержкой .env
python chatbot_with_env.py
```

## 5. Использование
1. Найдите бота в Telegram
2. Отправьте `/start`
3. Начните общение!

## Получение токенов

### Telegram Bot Token
1. Найдите @BotFather в Telegram
2. `/newbot` → следуйте инструкциям
3. Скопируйте токен

### OpenAI API Key
1. Зарегистрируйтесь на platform.openai.com
2. API Keys → Create new secret key
3. Скопируйте ключ
