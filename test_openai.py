import os
from openai import OpenAI

# Попытка загрузить переменные из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Для загрузки .env файла установите python-dotenv: pip install python-dotenv")

def test_openai_connection():
    """Тестирует подключение к OpenAI API"""
    
    # Получение API ключа
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Ошибка: Не установлена переменная окружения OPENAI_API_KEY")
        return False
    
    try:
        # Инициализация клиента
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.proxyapi.ru/openai/v1",
        )
        
        # Тестовый запрос
        print("🔄 Тестирование подключения к OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты вежливый и профессиональный личный помощник."},
                {"role": "user", "content": "Привет! Как дела?"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("✅ Подключение к OpenAI успешно!")
        print(f"📝 Ответ: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к OpenAI: {e}")
        return False

if __name__ == "__main__":
    test_openai_connection()
