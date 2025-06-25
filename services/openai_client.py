"""
Модуль services/openai_client.py

Клиент для взаимодействия с OpenAI API.
Обеспечивает:
- Базовые запросы к ChatGPT
- Генерацию случайных фактов
- Ответы в стиле выбранной личности
"""

import logging
from typing import Optional
import openai
from config import CHATGPT_TOKEN

logger = logging.getLogger(__name__)

# Инициализация клиента OpenAI
client = openai.OpenAI(api_key=CHATGPT_TOKEN)

# Константы
DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000
ERROR_MESSAGE = "Извините, произошла ошибка при обработке вашего запроса."

async def get_chatgpt_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS
) -> str:
    """
    Отправляет запрос к ChatGPT и возвращает ответ.

    Args:
        prompt: Основной промпт пользователя.
        system_prompt: Системный промпт (опционально).
        model: Модель GPT для использования.
        temperature: Креативность ответа (0-2).
        max_tokens: Максимальное количество токенов в ответе.

    Returns:
        str: Ответ от ChatGPT или сообщение об ошибке.
    """
    try:
        messages = [{"role": "user", "content": prompt}]

        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Ошибка запроса к OpenAI: {e}", exc_info=True)
        return ERROR_MESSAGE

async def get_random_fact() -> str:
    """
    Генерирует случайный научный факт.

    Returns:
        str: Короткий интересный факт.
    """
    prompt = (
        "Расскажи один интересный и малоизвестный научный факт. "
        "Факт должен быть коротким (1-2 предложения), но содержательным. "
        "Избегай общеизвестных фактов."
    )
    return await get_chatgpt_response(prompt)

async def get_personality_response(
    message: str,
    personality_prompt: str,
    model: str = DEFAULT_MODEL
) -> str:
    """
    Получает ответ в стиле выбранной личности.

    Args:
        message: Сообщение пользователя.
        personality_prompt: Промпт, определяющий личность.
        model: Модель GPT для использования.

    Returns:
        str: Ответ в стиле выбранной личности.
    """
    return await get_chatgpt_response(
        prompt=message,
        system_prompt=personality_prompt,
        model=model
    )