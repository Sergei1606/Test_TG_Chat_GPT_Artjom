import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import get_chatgpt_response

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
SELECTING_LANGUAGE, TRANSLATING_TEXT = range(2)

# Доступные языки перевода
LANGUAGES = {
    "en": "Английский 🇬🇧",
    "ru": "Русский 🇷🇺",
    "et": "Эстонский 🇪🇪",
    "de": "Немецкий 🇩🇪",
    "fr": "Французский 🇫🇷"
}


async def translate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с переводчиком"""
    try:
        # Загружаем изображение для интерфейса
        image_path = "data/images/translate.jpeg"
        caption = (
            "🌍 <b>Переводчик текста</b>\n\n"
            "Выберите язык, на который нужно перевести текст:"
        )

        # Создаем клавиатуру с кнопками выбора языка
        keyboard = []
        for lang_code, lang_name in LANGUAGES.items():
            keyboard.append([InlineKeyboardButton(lang_name, callback_data=f"lang_{lang_code}")])

        keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="cancel_translate")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                if update.callback_query:
                    await update.callback_query.message.reply_photo(
                        photo=photo,
                        caption=caption,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                    await update.callback_query.answer()
                else:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=caption,
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
        else:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    caption,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                await update.callback_query.answer()
            else:
                await update.message.reply_text(
                    caption,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )

        return SELECTING_LANGUAGE

    except Exception as e:
        logger.error(f"Ошибка при запуске переводчика: {e}")
        error_text = "😔 Произошла ошибка при запуске переводчика. Попробуйте позже."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)
        return ConversationHandler.END


async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора языка"""
    query = update.callback_query
    await query.answer()

    lang_code = query.data.replace("lang_", "")
    context.user_data['target_language'] = lang_code
    lang_name = LANGUAGES.get(lang_code, "выбранный язык")

    await query.edit_message_text(
        f"🌍 Выбран язык: <b>{lang_name}</b>\n\n"
        "Теперь отправьте текст, который нужно перевести:",
        parse_mode='HTML'
    )

    return TRANSLATING_TEXT


async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перевод текста"""
    try:
        user_text = update.message.text
        lang_code = context.user_data.get('target_language', 'en')
        lang_name = LANGUAGES.get(lang_code, "выбранный язык")

        # Показываем статус "печатает"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        # Формируем запрос для ChatGPT
        prompt = (
            f"Переведи следующий текст на {lang_name}. "
            f"Сохрани исходное форматирование (абзацы, списки и т.д.):\n\n{user_text}"
        )

        # Получаем перевод
        translation = await get_chatgpt_response(prompt)

        # Создаем кнопки для продолжения
        keyboard = [
            [InlineKeyboardButton("🔄 Сменить язык", callback_data="change_language")],
            [InlineKeyboardButton("🏁 Закончить", callback_data="finish_translate")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🌍 <b>Перевод на {lang_name}:</b>\n\n{translation}",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

        return TRANSLATING_TEXT

    except Exception as e:
        logger.error(f"Ошибка при переводе текста: {e}")
        await update.message.reply_text(
            "😔 Произошла ошибка при переводе. Попробуйте еще раз."
        )
        return TRANSLATING_TEXT


async def handle_translate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок в переводчике"""
    query = update.callback_query
    await query.answer()

    if query.data == "change_language":
        return await translate_start(update, context)
    elif query.data in ["cancel_translate", "finish_translate"]:
        await query.edit_message_text(
            "🏠 Возвращаемся в главное меню...",
            parse_mode='HTML'
        )
        return ConversationHandler.END

    return TRANSLATING_TEXT