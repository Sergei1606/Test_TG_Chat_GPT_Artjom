# 🤖 Telegram ChatGPT Bot 
Многофункциональный Telegram-бот с интеграцией ChatGPT, 
диалогами с историческими личностями, квизами и другими возможностями.

## 🌟 Возможности

- **ChatGPT**: Общение с ИИ в реальном времени
- **Диалоги с личностями**: Общайтесь с Эйнштейном, Шекспиром и другими
- **Квизы**: Тесты по программированию, истории и науке
- **Рандомные факты**: Интересные научные факты
- **Переводчик**: Многоязычный перевод текстов
- **Помощник по резюме**: Генерация профессиональных резюме

## Требования
- Python 3.8+
- Poetry (для управления зависимостями)
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- OpenAI API Key

## 1. Клонирование репозитория
```bash
git clone https://github.com/ваш-репозиторий/Test_TG_Chat_GPT_Artjom.git
cd Test_TG_Chat_GPT_Artjom

## ⚙️ Установка зависимостей
poetry install


## Настройка окружения
Заполни .env.example ПЕРЕД СТАРТОМ 
CHATGPT_TOKEN=""
TG_BOT_TOKEN=""
(или создай на его основе свою папку .env  в корне )

🏃 Запуск
poetry run python main.py

или
python main.py


 

структура проекта (с пояснениями)

telegram_gpt_bot/  
│
├── .env                    # Секретные ключи (BOT_TOKEN, OPENAI_API_KEY и др.)
├── .env.example            # Шаблон для .env с примерами переменных
├── .gitignore              
│
├── data/ 
│   └──images/ 
│   └── personalities.py
│   └── quiz_topics.py
│
├── config/                 # Конфигурация проекта
│   ├── __init__.py
│   └── settings.py         # Загрузка переменных окружения и настройки
│
├── data/                   # Данные бота ( базы данных и т.д.)
│   ├── personalities.json  # Пресеты персонажей для чата
│   └── quiz_topics.json    # Темы для викторин
│
├── handlers/               # Обработчики команд и сообщений
│   ├── __init__.py
│   ├── basic.py            # Старт, помощь, ошибки
│   ├── chatgpt_interface.py # Основной чат с GPT
│   ├── personality_chat.py # Общение в стиле персонажа
│   ├── quiz.py             # Викторины
│   ├── random_fact.py      # Случайные факты
│   ├── resume.py           # Резюме/профиль
│   └── translate.py        # Перевод текста
│
├── services/               # Внешние сервисы и API
│   ├── __init__.py
│   └── openai_client.py    # Логика запросов к OpenAI
│
├── utils/                  # Вспомогательные модули
│   ├── __init__.py
│   ├── logger.py           # Настройка логов
│   └── helpers.py          # Утилиты (например, загрузка JSON из data/)
│
├── main.py                 # Точка входа (запуск бота)
├── poetry.lock             # Зависимости Poetry
├── pyproject.toml          # Конфигурация Poetry (зависимости, версии)
└── README.md               # Описание проекта, инструкции


