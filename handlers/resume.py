"""
Модуль handlers/resume.py

Обработчик для создания профессиональных резюме.
Позволяет пользователю ввести данные о себе и генерирует
форматированное резюме с помощью ChatGPT.
Использует ConversationHandler для пошагового взаимодействия.
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import get_chatgpt_response

logger = logging.getLogger(__name__)

# Состояния ConversationHandler
GETTING_NAME, GETTING_EDUCATION, GETTING_EXPERIENCE, GETTING_SKILLS, GENERATING_RESUME = range(5)

# Константы
RESUME_IMAGE_PATH = "data/images/resume.jpeg"
DEFAULT_ERROR_MSG = "😔 Произошла ошибка. Попробуйте позже."

# Тексты интерфейса
START_TEXT = """
📄 <b>Помощник по составлению резюме</b>\n\n
Я помогу вам создать профессиональное резюме.\n\n
Для начала, введите ваше <b>ФИО</b> (например: Иванов Иван Иванович):"""

EDUCATION_TEXT = """
🎓 Теперь введите информацию о вашем <b>образовании</b>:
(Укажите учебные заведения, годы обучения, специальности)"""

EXPERIENCE_TEXT = """
💼 Введите информацию о вашем <b>опыте работы</b>:
(Укажите места работы, должности, периоды работы и обязанности)"""

SKILLS_TEXT = """
🛠️ Введите ваши <b>навыки и умения</b>:
(Перечислите через запятую или в виде списка)"""

# Клавиатуры
RESUME_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 Создать новое резюме", callback_data="new_resume")],
    [InlineKeyboardButton("🏁 Закончить", callback_data="finish_resume")]
])


async def resume_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Начинает процесс создания резюме.

    Args:
        update: Объект Update от Telegram API.
        context: Контекст бота.

    Returns:
        int: Первое состояние (GETTING_NAME) или ConversationHandler.END при ошибке.
    """
    try:
        if os.path.exists(RESUME_IMAGE_PATH):
            with open(RESUME_IMAGE_PATH, 'rb') as photo:
                if update.callback_query:
                    await update.callback_query.message.reply_photo(
                        photo=photo,
                        caption=START_TEXT,
                        parse_mode='HTML'
                    )
                    await update.callback_query.answer()
                else:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=START_TEXT,
                        parse_mode='HTML'
                    )
        else:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    START_TEXT,
                    parse_mode='HTML'
                )
                await update.callback_query.answer()
            else:
                await update.message.reply_text(
                    START_TEXT,
                    parse_mode='HTML'
                )

        return GETTING_NAME

    except Exception as e:
        logger.error(f"Ошибка в resume_start: {e}", exc_info=True)
        await _send_error_response(update)
        return ConversationHandler.END


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Получает ФИО пользователя и запрашивает информацию об образовании.

    Args:
        update: Объект Update с сообщением.
        context: Контекст бота.

    Returns:
        int: Следующее состояние (GETTING_EDUCATION).
    """
    context.user_data['resume'] = {'name': update.message.text}
    await update.message.reply_text(EDUCATION_TEXT, parse_mode='HTML')
    return GETTING_EDUCATION


async def get_education(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Получает информацию об образовании и запрашивает опыт работы.

    Args:
        update: Объект Update с сообщением.
        context: Контекст бота.

    Returns:
        int: Следующее состояние (GETTING_EXPERIENCE).
    """
    context.user_data['resume']['education'] = update.message.text
    await update.message.reply_text(EXPERIENCE_TEXT, parse_mode='HTML')
    return GETTING_EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Получает информацию об опыте работы и запрашивает навыки.

    Args:
        update: Объект Update с сообщением.
        context: Контекст бота.

    Returns:
        int: Следующее состояние (GETTING_SKILLS).
    """
    context.user_data['resume']['experience'] = update.message.text
    await update.message.reply_text(SKILLS_TEXT, parse_mode='HTML')
    return GETTING_SKILLS


async def get_skills(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Получает информацию о навыках и генерирует резюме через ChatGPT.

    Args:
        update: Объект Update с сообщением.
        context: Контекст бота.

    Returns:
        int: Состояние GENERATING_RESUME или ConversationHandler.END при ошибке.
    """
    try:
        context.user_data['resume']['skills'] = update.message.text

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        prompt = _build_resume_prompt(context.user_data['resume'])
        resume_text = await get_chatgpt_response(prompt)

        await update.message.reply_text(
            f"📄 <b>Ваше резюме:</b>\n\n{resume_text}",
            parse_mode='HTML',
            reply_markup=RESUME_KEYBOARD
        )

        return GENERATING_RESUME

    except Exception as e:
        logger.error(f"Ошибка в get_skills: {e}", exc_info=True)
        await update.message.reply_text(DEFAULT_ERROR_MSG)
        return ConversationHandler.END


async def handle_resume_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает callback-кнопки в процессе создания резюме.

    Args:
        update: Объект Update с callback_query.
        context: Контекст бота.

    Returns:
        int: Состояние или ConversationHandler.END.
    """
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "new_resume":
            context.user_data.pop('resume', None)
            return await resume_start(update, context)
        elif query.data == "finish_resume":
            await query.edit_message_text("🏠 Возвращаемся в главное меню...")
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"Ошибка в handle_resume_callback: {e}", exc_info=True)

    return GENERATING_RESUME


def _build_resume_prompt(resume_data: dict) -> str:
    """
    Формирует промпт для ChatGPT на основе данных пользователя.

    Args:
        resume_data: Словарь с данными для резюме.

    Returns:
        str: Сформированный промпт.
    """
    return (
        "Создай профессиональное резюме на основе следующих данных:\n\n"
        f"ФИО: {resume_data['name']}\n"
        f"Образование: {resume_data['education']}\n"
        f"Опыт работы: {resume_data['experience']}\n"
        f"Навыки: {resume_data['skills']}\n\n"
        "Формат резюме:\n"
        "1. ФИО (заголовок)\n"
        "2. Контактная информация (укажи примерные данные)\n"
        "3. Цель (сгенерируй подходящую)\n"
        "4. Образование\n"
        "5. Опыт работы\n"
        "6. Навыки\n"
        "7. Дополнительная информация (языки, сертификаты и т.д.)\n\n"
        "Используй профессиональный тон, маркированные списки и четкую структуру."
    )


async def _send_error_response(update: Update) -> None:
    """
    Отправляет сообщение об ошибке с учетом типа Update.

    Args:
        update: Объект Update.
    """
    if update.callback_query:
        await update.callback_query.edit_message_text(DEFAULT_ERROR_MSG)
    else:
        await update.message.reply_text(DEFAULT_ERROR_MSG)