"""
Модуль handlers/personality_chat.py

Обработчик диалога с историческими личностями через ChatGPT.
Реализует выбор персонажа и ведение стилизованного диалога в его манере.
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.openai_client import get_personality_response
from data.personalities import get_personality_keyboard, get_personality_data
from handlers.basic import start

logger = logging.getLogger(__name__)

# Состояния ConversationHandler
SELECTING_PERSONALITY, CHATTING_WITH_PERSONALITY = range(2)

# Константы
PERSONALITY_IMAGE_PATH = "data/images/personality.jpeg"
DEFAULT_ERROR_MESSAGE = "😔 Произошла ошибка. Попробуйте позже."


async def talk_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команды /talk. Перенаправляет в talk_start().

    Args:
        update: Объект Update от Telegram API.
        context: Контекст бота (ContextTypes.DEFAULT_TYPE).

    Returns:
        int: Следующее состояние ConversationHandler.
    """
    return await talk_start(update, context)


async def talk_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запускает интерфейс выбора личности, отправляя меню с вариантами.

    Args:
        update: Объект Update от Telegram API.
        context: Контекст бота.

    Returns:
        int: Состояние SELECTING_PERSONALITY или -1 при ошибке.

    Raises:
        Exception: Логирует ошибки при отправке сообщения.
    """
    try:
        message_text = (
            "👥 <b>Диалог с известной личностью</b>\n\n"
            "Выберите, с кем хотите поговорить:\n\n"
            "🧬 <b>Альберт Эйнштейн</b> - физика и философия\n"
            "🎭 <b>Уильям Шекспир</b> - поэзия и драматургия\n"
            "🎨 <b>Леонардо да Винчи</b> - искусство и изобретения\n"
            "📱 <b>Стив Джобс</b> - технологии и инновации\n"
            "📝 <b>Александр Пушкин</b> - русская поэзия\n\n"
            "Выберите личность:"
        )

        keyboard = get_personality_keyboard()

        if update.callback_query:
            if os.path.exists(PERSONALITY_IMAGE_PATH):
                await update.callback_query.message.delete()
                with open(PERSONALITY_IMAGE_PATH, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=update.callback_query.message.chat_id,
                        photo=photo,
                        caption=message_text,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
            else:
                await update.callback_query.edit_message_text(
                    message_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            await update.callback_query.answer()
        else:
            if os.path.exists(PERSONALITY_IMAGE_PATH):
                with open(PERSONALITY_IMAGE_PATH, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=message_text,
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )
            else:
                await update.message.reply_text(
                    message_text,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )

        return SELECTING_PERSONALITY

    except Exception as e:
        logger.error(f"Ошибка в talk_start: {e}", exc_info=True)
        await send_error_response(update, context)
        return -1


async def personality_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор конкретной личности пользователем.

    Args:
        update: Объект Update с callback_query.
        context: Контекст бота.

    Returns:
        int: Состояние CHATTING_WITH_PERSONALITY или -1 при ошибке.
    """
    query = update.callback_query
    await query.answer()

    try:
        personality_key = query.data.replace("personality_", "")
        personality = get_personality_data(personality_key)

        if not personality:
            await edit_or_send_message(
                query,
                "❌ Ошибка: личность не найдена.",
                has_photo=bool(query.message.photo)
            )
            return -1

        context.user_data.update({
            'current_personality': personality_key,
            'personality_data': personality
        })

        message_text = (
            f"{personality['emoji']} <b>Диалог с {personality['name']}</b>\n\n"
            f"Теперь вы можете общаться с {personality['name']}!\n\n"
            "💬 Просто напишите ваше сообщение, и личность ответит в своем стиле.\n\n"
            "✍️ Напишите что-нибудь:"
        )

        await edit_or_send_message(
            query,
            message_text,
            has_photo=bool(query.message.photo)
        )

        return CHATTING_WITH_PERSONALITY

    except Exception as e:
        logger.error(f"Ошибка в personality_selected: {e}", exc_info=True)
        await send_error_response(update, context)
        return -1


async def handle_personality_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает текстовое сообщение для выбранной личности.

    Args:
        update: Объект Update с сообщением пользователя.
        context: Контекст бота.

    Returns:
        int: Состояние CHATTING_WITH_PERSONALITY.
    """
    try:
        personality_data = context.user_data.get('personality_data')
        if not personality_data:
            await update.message.reply_text("❌ Личность не выбрана. Используйте /talk")
            return -1

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        processing_msg = await update.message.reply_text(
            f"{personality_data['emoji']} {personality_data['name']} размышляет... ⏳"
        )

        response = await get_personality_response(
            update.message.text,
            personality_data['prompt']
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 Продолжить", callback_data="continue_chat")],
            [InlineKeyboardButton("👥 Сменить личность", callback_data="change_personality")],
            [InlineKeyboardButton("🏠 Выход", callback_data="finish_talk")]
        ])

        await processing_msg.delete()
        await update.message.reply_text(
            f"{personality_data['emoji']} <b>{personality_data['name']} отвечает:</b>\n\n{response}",
            parse_mode='HTML',
            reply_markup=keyboard
        )

        return CHATTING_WITH_PERSONALITY

    except Exception as e:
        logger.error(f"Ошибка в handle_personality_message: {e}", exc_info=True)
        await update.message.reply_text(DEFAULT_ERROR_MESSAGE)
        return CHATTING_WITH_PERSONALITY


async def handle_personality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает callback-кнопки в диалоге с личностью.

    Args:
        update: Объект Update с callback_query.
        context: Контекст бота.

    Returns:
        int: Новое состояние ConversationHandler.
    """
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "continue_chat":
            personality_data = context.user_data.get('personality_data')
            if personality_data:
                await query.edit_message_text(
                    f"{personality_data['emoji']} <b>Продолжаем с {personality_data['name']}</b>\n\n"
                    "💬 Ваше следующее сообщение:",
                    parse_mode='HTML'
                )
            return CHATTING_WITH_PERSONALITY

        elif query.data == "change_personality":
            return await talk_start(update, context)

        elif query.data == "finish_talk":
            context.user_data.clear()
            return -1

    except Exception as e:
        logger.error(f"Ошибка в handle_personality_callback: {e}", exc_info=True)

    return CHATTING_WITH_PERSONALITY


async def edit_or_send_message(query, text: str, has_photo: bool = False) -> None:
    """
    Вспомогательная функция для редактирования сообщения с фото или без.

    Args:
        query: CallbackQuery объект.
        text: Текст сообщения.
        has_photo: Флаг наличия фото в исходном сообщении.
    """
    if has_photo:
        await query.edit_message_caption(caption=text, parse_mode='HTML')
    else:
        await query.edit_message_text(text=text, parse_mode='HTML')


async def send_error_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет стандартное сообщение об ошибке.

    Args:
        update: Объект Update.
        context: Контекст бота.
    """
    try:
        if update.callback_query:
            if update.callback_query.message.photo:
                await update.callback_query.edit_message_caption(DEFAULT_ERROR_MESSAGE)
            else:
                await update.callback_query.edit_message_text(DEFAULT_ERROR_MESSAGE)
        else:
            await update.message.reply_text(DEFAULT_ERROR_MESSAGE)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")