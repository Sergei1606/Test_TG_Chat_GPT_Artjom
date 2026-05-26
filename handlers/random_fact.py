import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.openai_client import get_random_fact

logger = logging.getLogger(__name__)


async def random_fact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /random"""
    try:
        image_path = "data/images/random_fact.jpeg"
        chat_id = update.effective_chat.id
        
        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                await context.bot.send_photo(chat_id=chat_id, photo=photo)
                
        loading_msg = await context.bot.send_message(chat_id=chat_id, text="🎲 Генерирую интересный факт... ⏳")
        fact = await get_random_fact()
        keyboard = [
                    [InlineKeyboardButton("🎲 Хочу ещё факт", callback_data="random_more")],
                    [InlineKeyboardButton("🏠 Закончить", callback_data="random_finish")]
                ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await loading_msg.edit_text(
            f"🧠 <b>Интересный факт:</b>\n\n{fact}",
            parse_mode='HTML',
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Ошибка при получении факта от OpenAI: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="🤔 К сожалению, не удалось получить факт в данный момент. Попробуйте позже!")


async def random_fact_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок для рандомных фактов"""
    query = update.callback_query
    await query.answer()

    if query.data == "random_more":
        await random_fact(update, context)

    elif query.data == "random_finish":
        from handlers.basic import start
        await start(update, context)

    elif query.data == "random_fact":
        await random_fact(update, context)
