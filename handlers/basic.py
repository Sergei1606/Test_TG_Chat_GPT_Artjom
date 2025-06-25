"""
Модуль handlers/basic.py

Базовые обработчики бота:
- Стартовое меню (/start)
- Навигация по главному меню
- Обработка ошибок
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Константы интерфейса
WELCOME_TEXT = """
🎉 <b>Добро пожаловать в ChatGPT бота!</b>

🚀 <b>Доступные функции:</b>
• 🎲 Рандомный факт — получи интересный факт
• 🤖 ChatGPT — общение с ИИ
• 👥 Диалог с личностью — говори с известными людьми
• 🧠 Квиз — проверь свои знания
• 🌍 Переводчик — переведи текст на другой язык
• 📄 Помощь с резюме — создай профессиональное резюме

Выберите функцию из меню ниже:
"""

# Клавиатура главного меню
MAIN_MENU_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
    [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_interface")],
    [InlineKeyboardButton("👥 Диалог с личностью", callback_data="talk_interface")],
    [InlineKeyboardButton("🧠 Квиз", callback_data="quiz_interface")],
    [InlineKeyboardButton("🌍 Переводчик", callback_data="translate_interface")],
    [InlineKeyboardButton("📄 Помощь с резюме", callback_data="resume_interface")]
])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик команды /start. Отображает главное меню.

    Args:
        update: Объект Update от Telegram API
        context: Контекст бота

    Обрабатывает:
        - Прямой вызов команды (/start)
        - Возврат в главное меню через кнопку
    """
    try:
        if update.message:
            await update.message.reply_text(
                WELCOME_TEXT,
                parse_mode='HTML',
                reply_markup=MAIN_MENU_KEYBOARD
            )
        elif update.callback_query:
            await _handle_callback_start(update.callback_query)

    except Exception as e:
        logger.error(f"Ошибка в start: {e}", exc_info=True)
        await _send_error_response(update)


async def _handle_callback_start(query) -> None:
    """
    Обрабатывает start для callback запросов.

    Args:
        query: Объект CallbackQuery
    """
    try:
        if query.message.text:
            await query.edit_message_text(
                WELCOME_TEXT,
                parse_mode='HTML',
                reply_markup=MAIN_MENU_KEYBOARD
            )
        else:
            await query.message.reply_text(
                WELCOME_TEXT,
                parse_mode='HTML',
                reply_markup=MAIN_MENU_KEYBOARD
            )
        await query.answer()
    except Exception as e:
        logger.error(f"Ошибка в callback start: {e}")
        await query.answer("⚠️ Произошла ошибка", show_alert=True)


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик кнопок главного меню.
    Перенаправляет в start() для обновления меню.
    """
    query = update.callback_query
    await query.answer()
    await start(update, context)


async def _send_error_response(update: Update) -> None:
    """
    Отправляет сообщение об ошибке с учетом типа Update.

    Args:
        update: Объект Update (может быть Message или CallbackQuery)
    """
    error_text = "⚠️ Произошла ошибка. Попробуйте позже."
    try:
        if update.callback_query:
            await update.callback_query.answer(error_text, show_alert=True)
        elif update.message:
            await update.message.reply_text(error_text)
    except Exception as e:
        logger.critical(f"Критическая ошибка отправки сообщения: {e}")