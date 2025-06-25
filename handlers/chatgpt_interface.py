"""
Модуль handlers/chatgpt_interface.py

Обработчик взаимодействия с ChatGPT для Telegram-бота.
Включает команду /gpt и диалоговый интерфейс с использованием ConversationHandler.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from services.openai_client import get_chatgpt_response

# Настройка логгера
logger = logging.getLogger(__name__)

# Состояния ConversationHandler
WAITING_FOR_MESSAGE = 1

CAPTION = """🤖 <b>ChatGPT Интерфейс</b>\n\n
Напишите любой вопрос или сообщение, и я передам его ChatGPT!\n\n
💡 <b>Примеры вопросов:</b>\n
• Объясни квантовую физику простыми словами\n
• Напиши короткий рассказ про кота\n
• Как приготовить пасту карбонара?\n
• Переведи фразу на английский\n\n
✍️ Просто напишите ваш вопрос следующим сообщением:"""


async def gpt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команды /gpt.
    Перенаправляет в основной обработчик gpt_start().

    Args:
        update: Объект Update от Telegram API.
        context: Контекст бота (ContextTypes.DEFAULT_TYPE).

    Returns:
        int: Следующее состояние ConversationHandler (WAITING_FOR_MESSAGE).
    """
    return await gpt_start(update, context)


async def gpt_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запускает ChatGPT интерфейс, отправляя приветственное сообщение с примерами.

    Args:
        update: Объект Update от Telegram API.
        context: Контекст бота (ContextTypes.DEFAULT_TYPE).

    Returns:
        int: Следующее состояние ConversationHandler (WAITING_FOR_MESSAGE).

    Raises:
        Exception: Логирует ошибку, если не удалось отправить сообщение.
    """
    try:
        message_text = CAPTION
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="gpt_cancel")]
        ])

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            await update.callback_query.answer()
        else:
            await update.message.reply_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )

        return WAITING_FOR_MESSAGE

    except Exception as e:
        logger.error(f"Ошибка в gpt_start: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Не удалось запустить ChatGPT. Попробуйте позже.")
        return ConversationHandler.END


async def handle_gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает текстовые сообщения пользователя для ChatGPT.

    Args:
        update: Объект Update с сообщением пользователя.
        context: Контекст бота.

    Returns:
        int: Следующее состояние (WAITING_FOR_MESSAGE).
    """
    try:
        user_message = update.message.text

        # Показываем статус "печатает"
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        # Получаем ответ от ChatGPT
        response = await get_chatgpt_response(user_message)

        # Создаем клавиатуру
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Новый запрос", callback_data="gpt_new")],
            [InlineKeyboardButton("❌ Закрыть", callback_data="gpt_finish")]
        ])

        # Отправляем ответ
        await update.message.reply_text(
            f"🤖 <b>Ответ ChatGPT:</b>\n\n{response}",
            parse_mode='HTML',
            reply_markup=keyboard
        )

        return WAITING_FOR_MESSAGE

    except Exception as e:
        logger.error(f"Ошибка в handle_gpt_message: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ Произошла ошибка при обработке запроса. Попробуйте еще раз."
        )
        return WAITING_FOR_MESSAGE


async def handle_gpt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает callback-кнопки в ChatGPT интерфейсе.

    Args:
        update: Объект Update с callback_query.
        context: Контекст бота.

    Returns:
        int: Следующее состояние или ConversationHandler.END.
    """
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "gpt_new":
            return await gpt_start(update, context)
        elif query.data in ["gpt_finish", "gpt_cancel"]:
            await query.edit_message_text("✅ Сеанс с ChatGPT завершен")
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"Ошибка в handle_gpt_callback: {e}", exc_info=True)

    return WAITING_FOR_MESSAGE