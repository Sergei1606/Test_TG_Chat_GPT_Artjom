"""Файл с базовыми хендлерами бота."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start."""
    keyboard = [
        [InlineKeyboardButton("🎲 Рандомный факт", callback_data="random_fact")],
        [InlineKeyboardButton("🤖 ChatGPT", callback_data="gpt_interface")],
        [InlineKeyboardButton("👥 Диалог с личностью", callback_data="talk_interface")],
        [InlineKeyboardButton("🧠 Квиз", callback_data="quiz_interface")],
        [InlineKeyboardButton("🌍 Переводчик", callback_data="translate_interface")],
        [InlineKeyboardButton("📄 Помощь с резюме", callback_data="resume_interface")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "🎉 <b>Добро пожаловать в ChatGPT бота!</b>\n\n"
        "🚀 <b>Доступные функции:</b>\n"
        "• 🎲 Рандомный факт — получи интересный факт\n"
        "• 🤖 ChatGPT — общение с ИИ\n"
        "• 👥 Диалог с личностью — говори с известными людьми\n"
        "• 🧠 Квиз — проверь свои знания\n"
        "• 🌍 Переводчик — переведи текст на другой язык\n"
        "• 📄 Помощь с резюме — создай профессиональное резюме\n\n"
        "Выберите функцию из меню ниже:"
    )

    try:
        if update.message:
            await update.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)
        elif update.callback_query:
            # Проверяем, есть ли текст в сообщении для редактирования
            if update.callback_query.message.text:
                await update.callback_query.edit_message_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await update.callback_query.message.reply_text(welcome_text, parse_mode='HTML', reply_markup=reply_markup)
            await update.callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка в start handler: {e}")
        if update.callback_query:
            await update.callback_query.answer("Произошла ошибка, попробуйте еще раз")

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий кнопок главного меню."""
    query = update.callback_query
    await query.answer()
    await start(update, context)