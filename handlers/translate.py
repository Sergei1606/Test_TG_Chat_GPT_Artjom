"""
Модуль handlers/translate.py

Обработчик для перевода текста между языками с помощью ChatGPT.
Поддерживает несколько языков, сохраняет форматирование исходного текста
и предоставляет удобный интерфейс для повторных переводов.
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from typing import Dict, Optional
from services.openai_client import get_chatgpt_response

logger = logging.getLogger(__name__)

# Состояния ConversationHandler
SELECTING_LANGUAGE, TRANSLATING_TEXT = range(2)

# Поддерживаемые языки
LANGUAGES: Dict[str, str] = {
    "en": "Английский 🇬🇧",
    "ru": "Русский 🇷🇺",
    "et": "Эстонский 🇪🇪",
    "de": "Немецкий 🇩🇪",
    "fr": "Французский 🇫🇷"
}

# Путь к изображению
TRANSLATE_IMAGE_PATH = os.path.join("data", "images", "translate.jpeg")

# Тексты интерфейса
START_TEXT = "🌍 <b>Переводчик текста</b>\n\nВыберите язык перевода:"
LANGUAGE_SELECTED_TEXT = "🌍 Выбран язык: <b>{}</b>\n\nОтправьте текст для перевода:"
TRANSLATION_RESULT_TEXT = "🌍 <b>Перевод ({}):</b>\n\n{}"
ERROR_TEXT = "⚠️ Не удалось выполнить перевод"


async def safe_send_translate_interface(update: Update, caption: str, reply_markup: InlineKeyboardMarkup) -> bool:
    """
    Безопасно отправляет интерфейс переводчика с обработкой ошибок.

    Args:
        update: Объект Update.
        caption: Текст сообщения.
        reply_markup: Клавиатура.

    Returns:
        bool: True если отправка прошла успешно.
    """
    try:
        if os.path.exists(TRANSLATE_IMAGE_PATH):
            try:
                with open(TRANSLATE_IMAGE_PATH, 'rb') as photo:
                    if update.callback_query:
                        await update.callback_query.message.reply_photo(
                            photo=photo,
                            caption=caption,
                            parse_mode='HTML',
                            reply_markup=reply_markup
                        )
                    else:
                        await update.message.reply_photo(
                            photo=photo,
                            caption=caption,
                            parse_mode='HTML',
                            reply_markup=reply_markup
                        )
                return True
            except Exception as e:
                logger.warning(f"Не удалось отправить фото: {e}")

        # Fallback на текстовый интерфейс
        if update.callback_query:
            await update.callback_query.edit_message_text(
                caption,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                caption,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        return True

    except Exception as e:
        logger.error(f"Ошибка отправки интерфейса: {e}", exc_info=True)
        return False


async def translate_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запускает процесс перевода, показывая меню выбора языка.

    Args:
        update: Объект Update.
        context: Контекст бота.

    Returns:
        int: Состояние SELECTING_LANGUAGE или ConversationHandler.END при ошибке.
    """
    try:
        keyboard = [
            [InlineKeyboardButton(text, callback_data=f"lang_{code}")]
            for code, text in LANGUAGES.items()
        ]
        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="cancel_translate")])

        if not await safe_send_translate_interface(
                update,
                START_TEXT,
                InlineKeyboardMarkup(keyboard)
        ):
            raise Exception("Не удалось отправить интерфейс")

        if update.callback_query:
            await update.callback_query.answer()
        return SELECTING_LANGUAGE

    except Exception as e:
        logger.error(f"Ошибка в translate_start: {e}", exc_info=True)
        await _send_error_response(update)
        return ConversationHandler.END


async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор языка пользователем.

    Args:
        update: Объект Update с callback_query.
        context: Контекст бота.

    Returns:
        int: Состояние TRANSLATING_TEXT.
    """
    query = update.callback_query
    await query.answer()

    lang_code = query.data.replace("lang_", "")
    context.user_data['target_language'] = lang_code
    lang_name = LANGUAGES.get(lang_code, lang_code)

    try:
        await query.edit_message_text(
            LANGUAGE_SELECTED_TEXT.format(lang_name),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")
        await query.message.reply_text(
            LANGUAGE_SELECTED_TEXT.format(lang_name),
            parse_mode='HTML'
        )

    return TRANSLATING_TEXT


async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Выполняет перевод текста с помощью ChatGPT.

    Args:
        update: Объект Update с сообщением.
        context: Контекст бота.

    Returns:
        int: Состояние TRANSLATING_TEXT.
    """
    try:
        user_text = update.message.text
        lang_code = context.user_data.get('target_language', 'en')
        lang_name = LANGUAGES.get(lang_code, lang_code)

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        prompt = (
            f"Переведи следующий текст на {lang_name}, сохраняя:\n"
            "1. Оригинальное форматирование\n"
            "2. Специальные символы\n"
            "3. Технические термины\n\n"
            f"Текст: {user_text}"
        )

        translation = await get_chatgpt_response(prompt)

        keyboard = [
            [InlineKeyboardButton("🔄 Сменить язык", callback_data="change_language")],
            [InlineKeyboardButton("❌ Завершить", callback_data="finish_translate")]
        ]

        await update.message.reply_text(
            TRANSLATION_RESULT_TEXT.format(lang_name, translation),
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Ошибка перевода: {e}", exc_info=True)
        await update.message.reply_text(ERROR_TEXT)

    return TRANSLATING_TEXT


async def handle_translate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает callback-кнопки переводчика.

    Args:
        update: Объект Update с callback_query.
        context: Контекст бота.

    Returns:
        int: Новое состояние или ConversationHandler.END.
    """
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "change_language":
            return await translate_start(update, context)
        elif query.data in ["cancel_translate", "finish_translate"]:
            await query.edit_message_text("✅ Сеанс перевода завершен")
            return ConversationHandler.END
    except Exception as e:
        logger.error(f"Ошибка обработки callback: {e}", exc_info=True)
        await _send_error_response(update)

    return TRANSLATING_TEXT


async def _send_error_response(update: Update) -> None:
    """
    Отправляет сообщение об ошибке с учетом типа Update.

    Args:
        update: Объект Update.
    """
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(ERROR_TEXT)
        elif update.message:
            await update.message.reply_text(ERROR_TEXT)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения об ошибке: {e}")