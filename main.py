"""
Главный модуль Telegram бота.

Содержит точку входа и конфигурацию всех обработчиков команд и состояний.
"""

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
from telegram.warnings import PTBUserWarning
from warnings import filterwarnings

# Импорт переменных конфигурации напрямую
from config import TG_BOT_TOKEN, CHATGPT_TOKEN
from handlers import (
    basic,
    random_fact,
    chatgpt_interface,
    personality_chat,
    quiz,
    translate,
    resume
)

# Игнорируем предупреждения PTB (для избежания лишних логов)
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# Настройка логирования (фиксированный уровень INFO)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO  # Упрощено - всегда INFO без DEBUG режима
)
logger = logging.getLogger(__name__)


def setup_handlers(application: Application) -> None:
    """Регистрирует все обработчики команд и состояний."""
    command_handlers = [
        ("start", basic.start),
        ("random", random_fact.random_fact),
        ("gpt", chatgpt_interface.gpt_command),
        ("personality", personality_chat.talk_command),
        ("quiz", quiz.quiz_command),
        ("translate", translate.translate_start),
        ("resume", resume.resume_start)
    ]

    for command, handler in command_handlers:
        application.add_handler(CommandHandler(command, handler))

    # Conversation Handlers
    application.add_handler(_create_gpt_conversation())
    application.add_handler(_create_personality_conversation())
    application.add_handler(_create_quiz_conversation())
    application.add_handler(_create_translate_conversation())
    application.add_handler(_create_resume_conversation())

    # Callback Handlers
    application.add_handler(CallbackQueryHandler(random_fact.random_fact_callback, pattern="^random_"))
    application.add_handler(CallbackQueryHandler(basic.menu_callback))


def _create_gpt_conversation() -> ConversationHandler:
    """Создает ConversationHandler для ChatGPT интерфейса."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(chatgpt_interface.gpt_start, pattern="^gpt_interface$")],
        states={
            chatgpt_interface.WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, chatgpt_interface.handle_gpt_message)
            ],
        },
        fallbacks=[
            CommandHandler("start", basic.start),
            CallbackQueryHandler(basic.menu_callback, pattern="^(gpt_finish|main_menu)$")
        ],
        per_message=True,
    )



def _create_personality_conversation() -> ConversationHandler:
    """Создает ConversationHandler для диалога с личностью."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(personality_chat.talk_start, pattern="^talk_interface$"),
            CommandHandler("talk", personality_chat.talk_command)
        ],
        states={
            personality_chat.SELECTING_PERSONALITY: [
                CallbackQueryHandler(personality_chat.personality_selected, pattern="^personality_")
            ],
            personality_chat.CHATTING_WITH_PERSONALITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, personality_chat.handle_personality_message),
                CallbackQueryHandler(personality_chat.handle_personality_callback,
                                     pattern="^(continue_chat|change_personality|finish_talk)$")
            ],
        },
        fallbacks=[
            CommandHandler("start", basic.start),
            CallbackQueryHandler(basic.menu_callback, pattern="^main_menu$")
        ],
    )


def _create_quiz_conversation() -> ConversationHandler:
    """Создает ConversationHandler для квиза."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(quiz.quiz_start, pattern="^quiz_interface$"),
            CommandHandler("quiz", quiz.quiz_command)
        ],
        states={
            quiz.SELECTING_TOPIC: [
                CallbackQueryHandler(quiz.topic_selected, pattern="^quiz_topic_")
            ],
            quiz.ANSWERING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, quiz.handle_quiz_answer),
                CallbackQueryHandler(quiz.handle_quiz_callback,
                                     pattern="^(quiz_continue_|quiz_change_topic|quiz_finish)$")
            ],
        },
        fallbacks=[
            CommandHandler("start", basic.start),
            CallbackQueryHandler(basic.menu_callback, pattern="^main_menu$")
        ],
    )


def _create_translate_conversation() -> ConversationHandler:
    """Создает ConversationHandler для переводчика."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(translate.translate_start, pattern="^translate_interface$"),
            CommandHandler("translate", translate.translate_start)
        ],
        states={
            translate.SELECTING_LANGUAGE: [
                CallbackQueryHandler(translate.select_language, pattern="^lang_")
            ],
            translate.TRANSLATING_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translate.translate_text),
                CallbackQueryHandler(translate.handle_translate_callback,
                                     pattern="^(change_language|finish_translate|cancel_translate)$")
            ],
        },
        fallbacks=[
            CommandHandler("start", basic.start),
            CallbackQueryHandler(basic.menu_callback, pattern="^main_menu$")
        ],
    )


def _create_resume_conversation() -> ConversationHandler:
    """Создает ConversationHandler для помощника по резюме."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(resume.resume_start, pattern="^resume_interface$"),
            CommandHandler("resume", resume.resume_start)
        ],
        states={
            resume.GETTING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, resume.get_name)],
            resume.GETTING_EDUCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, resume.get_education)],
            resume.GETTING_EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, resume.get_experience)],
            resume.GETTING_SKILLS: [MessageHandler(filters.TEXT & ~filters.COMMAND, resume.get_skills)],
            resume.GENERATING_RESUME: [
                CallbackQueryHandler(resume.handle_resume_callback,
                                     pattern="^(new_resume|finish_resume)$")
            ],
        },
        fallbacks=[
            CommandHandler("start", basic.start),
            CallbackQueryHandler(basic.menu_callback, pattern="^cancel_resume$")
        ],
    )


def main() -> None:
    """Основная функция запуска бота."""
    try:
        # Создаем приложение бота (используем TG_BOT_TOKEN напрямую)
        application = Application.builder().token(TG_BOT_TOKEN).build()

        # Настройка обработчиков
        setup_handlers(application)

        # Обработчик ошибок
        application.add_error_handler(
            lambda update, context: logger.error(f"Update {update} caused error {context.error}"))

        # Запуск бота
        logger.info("Бот запущен успешно!")
        application.run_polling()

    except Exception as e:
        logger.critical(f'Критическая ошибка при запуске бота: {e}', exc_info=True)
        raise


if __name__ == "__main__":
    main()