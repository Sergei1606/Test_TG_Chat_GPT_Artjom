import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from services.openai_client import get_chatgpt_response
import os

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
GETTING_NAME, GETTING_EDUCATION, GETTING_EXPERIENCE, GETTING_SKILLS, GENERATING_RESUME = range(5)


async def resume_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало работы с помощником по резюме"""
    try:
        image_path = "data/images/resume.jpeg"
        caption = (
            "📄 <b>Помощник по составлению резюме</b>\n\n"
            "Я помогу вам создать профессиональное резюме.\n\n"
            "Для начала, введите ваше <b>ФИО</b> (например: Иванов Иван Иванович):"
        )

        if os.path.exists(image_path):
            with open(image_path, 'rb') as photo:
                if update.callback_query:
                    await update.callback_query.message.reply_photo(
                        photo=photo,
                        caption=caption,
                        parse_mode='HTML'
                    )
                    await update.callback_query.answer()
                else:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=caption,
                        parse_mode='HTML'
                    )
        else:
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    caption,
                    parse_mode='HTML'
                )
                await update.callback_query.answer()
            else:
                await update.message.reply_text(
                    caption,
                    parse_mode='HTML'
                )

        return GETTING_NAME

    except Exception as e:
        logger.error(f"Ошибка при запуске помощника по резюме: {e}")
        error_text = "😔 Произошла ошибка при запуске. Попробуйте позже."
        if update.callback_query:
            await update.callback_query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)
        return ConversationHandler.END


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение имени пользователя"""
    context.user_data['resume'] = {'name': update.message.text}

    await update.message.reply_text(
        "🎓 Теперь введите информацию о вашем <b>образовании</b>:\n"
        "(Укажите учебные заведения, годы обучения, специальности)",
        parse_mode='HTML'
    )

    return GETTING_EDUCATION


async def get_education(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение информации об образовании"""
    context.user_data['resume']['education'] = update.message.text

    await update.message.reply_text(
        "💼 Введите информацию о вашем <b>опыте работы</b>:\n"
        "(Укажите места работы, должности, периоды работы и обязанности)",
        parse_mode='HTML'
    )

    return GETTING_EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение информации об опыте работы"""
    context.user_data['resume']['experience'] = update.message.text

    await update.message.reply_text(
        "🛠️ Введите ваши <b>навыки и умения</b>:\n"
        "(Перечислите через запятую или в виде списка)",
        parse_mode='HTML'
    )

    return GETTING_SKILLS


async def get_skills(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение информации о навыках и генерация резюме"""
    context.user_data['resume']['skills'] = update.message.text

    # Показываем статус "печатает"
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Формируем запрос для ChatGPT
    prompt = (
        "Создай профессиональное резюме на основе следующих данных:\n\n"
        f"ФИО: {context.user_data['resume']['name']}\n"
        f"Образование: {context.user_data['resume']['education']}\n"
        f"Опыт работы: {context.user_data['resume']['experience']}\n"
        f"Навыки: {context.user_data['resume']['skills']}\n\n"
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

    # Получаем резюме от ChatGPT
    resume_text = await get_chatgpt_response(prompt)

    # Создаем кнопки для продолжения
    keyboard = [
        [InlineKeyboardButton("🔄 Создать новое резюме", callback_data="new_resume")],
        [InlineKeyboardButton("🏁 Закончить", callback_data="finish_resume")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"📄 <b>Ваше резюме:</b>\n\n{resume_text}",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

    return GENERATING_RESUME


async def handle_resume_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопок в помощнике по резюме"""
    query = update.callback_query
    await query.answer()

    if query.data == "new_resume":
        # Очищаем данные предыдущего резюме
        context.user_data.pop('resume', None)
        return await resume_start(update, context)
    elif query.data == "finish_resume":
        await query.edit_message_text(
            "🏠 Возвращаемся в главное меню...",
            parse_mode='HTML'
        )
        return ConversationHandler.END

    return GENERATING_RESUME