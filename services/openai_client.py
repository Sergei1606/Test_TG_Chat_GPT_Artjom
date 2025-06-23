import openai
import logging
from config import CHATGPT_TOKEN
from typing import Optional

logger = logging.getLogger(__name__)

# Инициализация клиента OpenAI для версии API >=1.0.0
client = openai.OpenAI(api_key=CHATGPT_TOKEN)


async def get_chatgpt_response(prompt: str, personality_prompt: Optional[str] = None) -> str:
    """Получить ответ от ChatGPT (совместимость с новой версией OpenAI API)"""
    try:
        messages = [{"role": "user", "content": prompt}]

        if personality_prompt:
            messages.insert(0, {"role": "system", "content": personality_prompt})

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
        return "Извините, произошла ошибка при обработке вашего запроса."


async def get_random_fact() -> str:
    """Получить случайный факт (обновленная версия)"""
    prompt = "Расскажи один интересный и малоизвестный научный факт. Факт должен быть коротким (1-2 предложения), но содержательным."
    return await get_chatgpt_response(prompt)


async def get_personality_response(message: str, personality_prompt: str) -> str:
    """Получить ответ от ChatGPT в стиле выбранной личности"""
    return await get_chatgpt_response(message, personality_prompt)