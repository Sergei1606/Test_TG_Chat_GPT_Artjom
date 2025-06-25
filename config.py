"""
Конфигурация бота - загрузка переменных окружения.
Простая версия без классов.
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Основные токены
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHATGPT_TOKEN = os.getenv("CHATGPT_TOKEN")

# Проверка обязательных переменных
if not TG_BOT_TOKEN:
    raise ValueError("Не указан TG_BOT_TOKEN в .env файле")
if not CHATGPT_TOKEN:
    raise ValueError("Не указан CHATGPT_TOKEN в .env файле")