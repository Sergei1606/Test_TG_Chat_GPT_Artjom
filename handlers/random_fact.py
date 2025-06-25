"""
Модуль handlers/random_fact.py

Обработчик генерации случайных интересных фактов.
Использует OpenAI API для получения фактов и предоставляет интерфейс для:
- Первичной генерации факта (/random_fact)
- Запроса дополнительных фактов (кнопка "Хочу ещё")
- Возврата в главное меню
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.openai_client import get_random_fact

logger = logging.getLogger(__name__)

# Константы
LOADING_TEXT = "🎲 Генерирую интересный факт... ⏳"
ERROR_TEXT = "😔 Произошла ошибка. Попробуйте позже."
FACT_TEMPLATE = "🧠 <b>Интересный факт:</b>\n\n{fact}"

# Клавиатуры
FACT_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🎲 Хочу ещё факт", callback_data="random_more")],
    [InlineKeyboardButton("🏠 Закончить", callback_data="random_finish")]
])

MAIN_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
    [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_interface")],
    [InlineKeyboardButton("👥 Диалог с личностью", callback_data="talk_interface")],
    [InlineKeyboardButton("🧠 Квиз", callback_data="quiz_interface")],
])


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /random_fact.
    Генерирует и отправляет случайный факт.

    Args:
        update: Объект Update от Telegram API.
        context: Контекст бота.
    """
    try:
        loading_msg = await update.message.reply_text(LOADING_TEXT)
        fact = await get_random_fact()
        await _send_fact_message(loading_msg, fact)

    except Exception as e:
        logger.error(f"Ошибка в random_fact: {e}", exc_info=True)
        await update.message.reply_text(
            "🤔 К сожалению, не удалось получить факт. Попробуйте позже!"
        )


async def random_fact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик callback-кнопок для работы с фактами.

    Args:
        update: Объект Update с callback_query.
        context: Контекст бота.
    """
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "random_more":
            await _handle_more_fact(query)
        elif query.data == "random_finish":
            await _return_to_main_menu(query)
        elif query.data == "random_fact":
            await _handle_new_fact(query)

    except Exception as e:
        logger.error(f"Ошибка в random_fact_callback: {e}", exc_info=True)
        await _edit_message_with_fallback(
            query,
            f"{ERROR_TEXT}\nИспользуйте /start чтобы вернуться в меню."
        )


async def _handle_more_fact(query) -> None:
    """
    Обрабатывает запрос на получение дополнительного факта.

    Args:
        query: CallbackQuery объект.
    """
    await query.edit_message_text(LOADING_TEXT)
    fact = await get_random_fact()
    await _send_fact_message(query, fact)


async def _handle_new_fact(query) -> None:
    """
    Обрабатывает запрос нового факта из главного меню.

    Args:
        query: CallbackQuery объект.
    """
    await query.edit_message_text(LOADING_TEXT)
    fact = await get_random_fact()
    await _send_fact_message(query, fact)


async def _return_to_main_menu(query) -> None:
    """
    Возвращает пользователя в главное меню.

    Args:
        query: CallbackQuery объект.
    """
    await query.edit_message_text(
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "Выберите одну из доступных функций:",
        parse_mode='HTML',
        reply_markup=MAIN_MENU_KEYBOARD
    )


async def _send_fact_message(target, fact: str) -> None:
    """
    Отправляет/редактирует сообщение с фактом.

    Args:
        target: Объект сообщения или callback_query.
        fact: Текст факта.
    """
    if hasattr(target, 'edit_message_text'):
        await target.edit_message_text(
            FACT_TEMPLATE.format(fact=fact),
            parse_mode='HTML',
            reply_markup=FACT_KEYBOARD
        )
    else:
        await target.reply_text(
            FACT_TEMPLATE.format(fact=fact),
            parse_mode='HTML',
            reply_markup=FACT_KEYBOARD
        )


async def _edit_message_with_fallback(query, text: str) -> None:
    """
    Редактирует сообщение с обработкой возможных ошибок.

    Args:
        query: CallbackQuery объект.
        text: Текст сообщения.
    """
    try:
        await query.edit_message_text(text)
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения: {e}")
        # Если не удалось отредактировать, пробуем отправить новое
        await query.message.reply_text(text)