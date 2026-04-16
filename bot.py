#!/usr/bin/env python3
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    raise ValueError("Please set TELEGRAM_TOKEN and GROQ_API_KEY in .env file")

groq_client = Groq(api_key=GROQ_API_KEY)
user_conversations = {}

def get_user_conversation(user_id: int):
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    return user_conversations[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_text = f"Привет, {user.first_name}! 👋\n\nЯ твой помощник для управления задачами!\n\n/help - помощь\n/мне - мои задачи\n/риск - анализ рисков\n/отчет - отчет\n/сброс - очистить историю"
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = "/мне - задачи\n/риск - анализ рисков\n/отчет - отчет\n/сброс - очистить историю\n\nПросто напиши что угодно - я помогу!"
    await update.message.reply_text(help_text)

async def my_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = "📋 ВАШ СПИСОК ЗАДАЧ:\n\n1. ✅ Интеграция API [HIGH]\n2. ⏳ Тестирование [MEDIUM]\n3. 🔄 Документация [LOW]\n\nИтого: 3 активных задачи"
    await update.message.reply_text(response)

async def risk_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=500,
            messages=[{"role": "user", "content": "Проанализируй риски в этих задачах: 1. API интеграция завтра, 2. Тестирование 3 дня, 3. Документация 5 дней. Дай 3 главных риска и рекомендации."}]
        )
        await update.message.reply_text(f"⚠️ АНАЛИЗ РИСКОВ:\n\n{response.choices[0].message.content}")
    except Exception as e:
        await update.message.reply_text("❌ Ошибка. Попробуй позже.")

async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=600,
            messages=[{"role": "user", "content": "Создай еженедельный отчет: выполнено 12 задач, осталось 8, скорость 2.4 в день, 3 перегруженных из 20."}]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text("❌ Ошибка. Попробуй позже.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_message = update.message.text
    conversation = get_user_conversation(user_id)
    conversation.append({"role": "user", "content": user_message})
    
    if len(conversation) > 10:
        conversation = conversation[-10:]
        user_conversations[user_id] = conversation

    try:
        await update.message.chat.send_action("typing")
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[{"role": "system", "content": "Ты помощник по управлению задачами. Помогаешь анализировать данные, даешь рекомендации. Отвечаешь кратко на русском."}] + conversation
        )
        ai_response = response.choices[0].message.content
        conversation.append({"role": "assistant", "content": ai_response})
        await update.message.reply_text(ai_response)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Ошибка. Попробуй позже.")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in user_conversations:
        user_conversations[user_id] = []
    await update.message.reply_text("✅ История очищена!")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mytasks", my_tasks))
    application.add_handler(CommandHandler("risk", risk_analysis))
    application.add_handler(CommandHandler("report", weekly_report))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot started. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
