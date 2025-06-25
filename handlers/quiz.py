"""
Модуль handlers/quiz.py

Обработчик интерактивных викторин с различными темами.
Позволяет пользователям выбирать тему, отвечать на вопросы и получать статистику.
Использует OpenAI для генерации вопросов и анализа ответов.
"""

import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from typing import Optional, Dict, Any
from services.openai_client import get_personality_response
from data.quiz_topics import get_quiz_topics_keyboard, get_quiz_topic_data, get_quiz_continue_keyboard

logger = logging.getLogger(__name__)

# Состояния ConversationHandler
SELECTING_TOPIC, ANSWERING_QUESTION = range(2)

# Константы
QUIZ_IMAGE_PATH = "data/images/quiz.png"
DEFAULT_ERROR_MESSAGE = "😔 Произошла ошибка. Попробуйте позже."

# Тексты интерфейса
QUIZ_START_TEXT = """
🧠 <b>Квиз - проверь свои знания!</b>\n\n
Выберите тему для квиза:\n\n
💻 <b>Программирование</b> - вопросы о коде и технологиях\n
🏛️ <b>История</b> - исторические факты и события\n
🔬 <b>Наука</b> - физика, химия, биология\n
🌍 <b>География</b> - страны, столицы, природа\n
🎬 <b>Кино</b> - фильмы и актеры\n\n
Выберите тему:"""


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработчик команды /quiz. Перенаправляет в quiz_start().

    Args:
        update: Объект Update от Telegram API.
        context: Контекст бота.

    Returns:
        int: Следующее состояние ConversationHandler.
    """
    logger.info('Обрабатываю команду /quiz')
    return await quiz_start(update, context)


async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Запускает квиз, отправляя меню выбора темы.

    Args:
        update: Объект Update.
        context: Контекст бота.

    Returns:
        int: Состояние SELECTING_TOPIC или -1 при ошибке.
    """
    try:
        logger.info(f'Попытка загрузить изображение: {QUIZ_IMAGE_PATH}')

        # Инициализация счетчика
        context.user_data.setdefault('quiz_score', 0)
        context.user_data.setdefault('quiz_total', 0)

        keyboard = get_quiz_topics_keyboard()

        if update.callback_query:
            await _send_or_edit_message(
                update.callback_query,
                QUIZ_START_TEXT,
                image_path=QUIZ_IMAGE_PATH,
                reply_markup=keyboard,
                is_edit=True
            )
        else:
            await _send_or_edit_message(
                update.message,
                QUIZ_START_TEXT,
                image_path=QUIZ_IMAGE_PATH,
                reply_markup=keyboard
            )

        return SELECTING_TOPIC

    except Exception as e:
        logger.error(f"Ошибка в quiz_start: {e}", exc_info=True)
        await _send_error_response(update, context)
        return -1


async def topic_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор темы пользователем.

    Args:
        update: Объект Update с callback_query.
        context: Контекст бота.

    Returns:
        int: Состояние ANSWERING_QUESTION или -1 при ошибке.
    """
    query = update.callback_query
    await query.answer()

    try:
        topic_key = query.data.replace("quiz_topic_", "")
        topic_data = get_quiz_topic_data(topic_key)

        if not topic_data:
            await _edit_message_content(query, "❌ Ошибка: тема не найдена.")
            return -1

        # Сохраняем данные темы
        context.user_data.update({
            'current_quiz_topic': topic_key,
            'quiz_topic_data': topic_data
        })

        # Генерируем вопрос
        processing_text = f"{topic_data['emoji']} Генерирую вопрос... ⏳"
        await _edit_message_content(query, processing_text)

        question = await get_personality_response(
            "Создай вопрос для квиза с 4 вариантами ответа (A-D)",
            topic_data['prompt']
        )

        # Извлекаем и сохраняем правильный ответ
        correct_answer = _extract_correct_answer(question)
        context.user_data.update({
            'current_question': question,
            'correct_answer': correct_answer
        })

        # Формируем текст вопроса
        question_text = (
            f"{topic_data['emoji']} <b>Квиз: {topic_data['name']}</b>\n\n"
            f"{question}\n\n"
            f"📊 <b>Счет:</b> {context.user_data['quiz_score']}/{context.user_data['quiz_total']}\n\n"
            "✍️ Напишите ваш ответ (A, B, C или D):"
        )

        await _edit_message_content(query, question_text)
        return ANSWERING_QUESTION

    except Exception as e:
        logger.error(f"Ошибка в topic_selected: {e}", exc_info=True)
        await _send_error_response(update, context)
        return -1


async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ответ пользователя на вопрос квиза.

    Args:
        update: Объект Update с сообщением.
        context: Контекст бота.

    Returns:
        int: Состояние ANSWERING_QUESTION или -1 при ошибке.
    """
    try:
        user_answer = update.message.text.strip().upper()
        correct_answer = context.user_data.get('correct_answer', '').upper()
        topic_data = context.user_data.get('quiz_topic_data')
        current_question = context.user_data.get('current_question', '')

        if not all([topic_data, correct_answer, current_question]):
            await update.message.reply_text("❌ Данные квиза не найдены. Используйте /quiz")
            return -1

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        # Проверяем ответ
        is_correct = user_answer == correct_answer
        context.user_data['quiz_total'] += 1
        if is_correct:
            context.user_data['quiz_score'] += 1

        # Получаем анализ ответа
        analysis = await _get_answer_analysis(
            user_answer,
            correct_answer,
            current_question,
            topic_data
        )

        # Формируем результат
        result_template = (
            "✅ <b>Правильно!</b>\n\n{analysis}" if is_correct else
            "❌ <b>Неправильно!</b>\n\nПравильный ответ: <b>{correct_answer}</b>\n\n{analysis}"
        )
        result_text = result_template.format(
            correct_answer=correct_answer,
            analysis=analysis
        )

        # Отправляем результат
        await update.message.reply_text(
            f"{topic_data['emoji']} <b>Результат</b>\n\n"
            f"{result_text}\n\n"
            f"📊 <b>Счет:</b> {context.user_data['quiz_score']}/{context.user_data['quiz_total']}",
            parse_mode='HTML',
            reply_markup=get_quiz_continue_keyboard(context.user_data['current_quiz_topic'])
        )

        return ANSWERING_QUESTION

    except Exception as e:
        logger.error(f"Ошибка в handle_quiz_answer: {e}", exc_info=True)
        await update.message.reply_text(DEFAULT_ERROR_MESSAGE)
        return ANSWERING_QUESTION


async def handle_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает callback-кнопки в квизе.

    Args:
        update: Объект Update с callback_query.
        context: Контекст бота.

    Returns:
        int: Новое состояние или -1 для завершения.
    """
    query = update.callback_query
    await query.answer()

    try:
        if query.data.startswith("quiz_continue_"):
            topic_key = query.data.replace("quiz_continue_", "")
            query.data = f"quiz_topic_{topic_key}"
            return await topic_selected(update, context)

        elif query.data == "quiz_change_topic":
            return await quiz_start(update, context)

        elif query.data == "quiz_finish":
            await _show_final_results(query, context)
            return -1

    except Exception as e:
        logger.error(f"Ошибка в handle_quiz_callback: {e}", exc_info=True)
        await _edit_message_content(query, DEFAULT_ERROR_MESSAGE)

    return ANSWERING_QUESTION


def _extract_correct_answer(question_text: str) -> str:
    """
    Извлекает правильный ответ из текста вопроса.

    Args:
        question_text: Текст вопроса с вариантами.

    Returns:
        str: Буква правильного ответа (A-D).
    """
    try:
        match = re.search(r'ответ:\s*([ABCD])', question_text, re.IGNORECASE)
        return match.group(1).upper() if match else 'A'
    except Exception as e:
        logger.error(f"Ошибка в _extract_correct_answer: {e}")
        return 'A'


async def _get_answer_analysis(
        user_answer: str,
        correct_answer: str,
        question: str,
        topic_data: Dict[str, Any]
) -> str:
    """
    Генерирует анализ ответа через OpenAI.

    Args:
        user_answer: Ответ пользователя.
        correct_answer: Правильный ответ.
        question: Текст вопроса.
        topic_data: Данные темы.

    Returns:
        str: Текст анализа.
    """
    prompt = f"""Пользователь ответил '{user_answer}' на вопрос:
    {question}

    Правильный ответ: {correct_answer}

    Дай краткое объяснение (2-3 предложения) и интересный факт по теме."""

    return await get_personality_response(
        prompt,
        "Ты эксперт по квизам, объясняешь ответы понятно и интересно."
    )


async def _show_final_results(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Показывает финальные результаты и очищает данные.

    Args:
        query: CallbackQuery объект.
        context: Контекст бота.
    """
    score = context.user_data.get('quiz_score', 0)
    total = max(context.user_data.get('quiz_total', 1), 1)
    percentage = round((score / total) * 100)

    # Определяем оценку
    if percentage >= 80:
        emoji, grade = "🏆", "Отлично!"
    elif percentage >= 60:
        emoji, grade = "🥈", "Хорошо!"
    elif percentage >= 40:
        emoji, grade = "🥉", "Неплохо!"
    else:
        emoji, grade = "📚", "Есть куда расти!"

    # Формируем текст
    final_text = (
        f"{emoji} <b>Квиз завершен!</b>\n\n"
        f"📊 <b>Результат:</b> {score}/{total} ({percentage}%)\n\n"
        f"<b>{grade}</b>\n\nСпасибо за участие! 🎉"
    )

    # Очищаем данные
    for key in ['quiz_score', 'quiz_total', 'current_quiz_topic',
                'quiz_topic_data', 'current_question', 'correct_answer']:
        context.user_data.pop(key, None)

    # Главное меню
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text, callback_data=cb)
         for text, cb in [
             ("🎲 Случайный факт", "random_interface"),
             ("🤖 ChatGPT", "gpt_interface"),
             ("👥 Диалог с личностью", "talk_interface"),
             ("🧠 Квиз", "quiz_interface")
         ]
         ]
    ])

    await query.edit_message_text(
        final_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )


async def _send_or_edit_message(
        target,
        text: str,
        image_path: str = None,
        reply_markup: InlineKeyboardMarkup = None,
        is_edit: bool = False
) -> None:
    """
    Универсальная функция для отправки/редактирования сообщений с возможностью прикрепления фото.

    Args:
        target: Объект сообщения или callback_query.
        text: Текст сообщения.
        image_path: Путь к изображению.
        reply_markup: Клавиатура.
        is_edit: Флаг редактирования.
    """
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as photo:
            if is_edit:
                await target.message.delete()
                await target.bot.send_photo(
                    chat_id=target.message.chat_id,
                    photo=photo,
                    caption=text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                await target.reply_photo(
                    photo=photo,
                    caption=text,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
    else:
        if is_edit:
            await target.edit_message_text(
                text=text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
        else:
            await target.reply_text(
                text=text,
                parse_mode='HTML',
                reply_markup=reply_markup
            )


async def _edit_message_content(query, text: str) -> None:
    """
    Редактирует сообщение с учетом типа контента (текст/фото).

    Args:
        query: CallbackQuery объект.
        text: Новый текст.
    """
    if query.message.photo:
        await query.edit_message_caption(caption=text, parse_mode='HTML')
    else:
        await query.edit_message_text(text=text, parse_mode='HTML')


async def _send_error_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Отправляет стандартное сообщение об ошибке.

    Args:
        update: Объект Update.
        context: Контекст бота.
    """
    try:
        if update.callback_query:
            await _edit_message_content(update.callback_query, DEFAULT_ERROR_MESSAGE)
        else:
            await update.message.reply_text(DEFAULT_ERROR_MESSAGE)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения об ошибке: {e}")