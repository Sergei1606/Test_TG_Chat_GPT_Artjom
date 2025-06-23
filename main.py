import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
from config import TG_BOT_TOKEN
from handlers import (
    basic,
    random_fact,
    chatgpt_interface,
    personality_chat,
    quiz,
    translate,
    resume
)
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning

# Игнорируем предупреждения PTB (для избежания лишних логов)
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Создаем приложение бота
        application = Application.builder().token(TG_BOT_TOKEN).build()

        # ===== Основные команды =====
        application.add_handler(CommandHandler("start", basic.start))
        application.add_handler(CommandHandler("random", random_fact.random_fact))
        application.add_handler(CommandHandler("gpt", chatgpt_interface.gpt_command))
        application.add_handler(CommandHandler("personality", personality_chat.talk_command))
        application.add_handler(CommandHandler("quiz", quiz.quiz_command))
        application.add_handler(CommandHandler("translate", translate.translate_start))
        application.add_handler(CommandHandler("resume", resume.resume_start))

        # ===== Обработчики состояний (ConversationHandler) =====

        # 1. ChatGPT интерфейс
        gpt_conversation = ConversationHandler(
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

        # 2. Диалог с личностью
        personality_conversation = ConversationHandler(
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

        # 3. Квиз
        quiz_conversation = ConversationHandler(
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

        # 4. Переводчик
        translate_conversation = ConversationHandler(
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

        # 5. Помощник по резюме
        resume_conversation = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(resume.resume_start, pattern="^resume_interface$"),
                CommandHandler("resume", resume.resume_start)
            ],
            states={
                resume.GETTING_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, resume.get_name)
                ],
                resume.GETTING_EDUCATION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, resume.get_education)
                ],
                resume.GETTING_EXPERIENCE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, resume.get_experience)
                ],
                resume.GETTING_SKILLS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, resume.get_skills)
                ],
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

        # ===== Регистрация обработчиков =====
        application.add_handler(gpt_conversation)
        application.add_handler(personality_conversation)
        application.add_handler(quiz_conversation)
        application.add_handler(translate_conversation)
        application.add_handler(resume_conversation)

        # Обработчики кнопок (без состояний)
        application.add_handler(CallbackQueryHandler(random_fact.random_fact_callback, pattern="^random_"))
        application.add_handler(CallbackQueryHandler(basic.menu_callback))
        application.add_error_handler(
            lambda update, context: logger.error(f"Update {update} caused error {context.error}"))

        # Запуск бота
        logger.info("Бот запущен успешно!")
        application.run_polling()

    except Exception as e:
        logger.error(f'Ошибка при запуске бота: {e}')

if __name__ == "__main__":
    main()
