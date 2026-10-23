"""Cycle Companion — Telegram bot. Answers your questions."""
import os
from datetime import date
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from chat.parser import parse_message
from chat.responses import (
    next_period_response, status_response, stats_response,
    history_response, unknown_response, serious_response,
    safety_check, late_response,
)
from cycle.calculator import calculate_cycle_lengths, current_cycle_day
from cycle.statistics import calculate_statistics
from cycle.predictor import predict_next_period
from cycle.phases import estimate_phase
from database import database as db

load_dotenv()


def build_reply(text, user_id):
    """Turn a user message into Cycle Companion's reply."""
    db.init_db()
    periods = db.get_periods(user_id)
    lengths = calculate_cycle_lengths(periods)
    stats = calculate_statistics(lengths)
    last_start = None
    if periods:
        last_start = date.fromisoformat(periods[-1]["start_date"])

    if safety_check(text):
        return serious_response()

    parsed = parse_message(text)
    intent = parsed["intent"]

    if intent == "START_PERIOD":
        open_period = db.get_last_period(user_id)
        if open_period and not open_period["end_date"]:
            db.update_period_end(user_id, open_period["id"], date.today())
        db.add_period(user_id, date.today())
        return "Logged. Period started today."

    if intent == "END_PERIOD":
        open_period = db.get_last_period(user_id)
        if open_period and not open_period["end_date"]:
            db.update_period_end(user_id, open_period["id"], date.today())
            return "Logged. Period ended today."
        return "No open period to close."

    if intent == "NEXT_PERIOD":
        return next_period_response(predict_next_period(lengths, last_start))

    if intent == "STATUS":
        cycle_day = current_cycle_day(last_start)
        typical = stats["weighted_median"] if stats else None
        return status_response(cycle_day, estimate_phase(cycle_day, typical), last_start)

    if intent == "STATS":
        return stats_response(stats)

    if intent == "HISTORY":
        return history_response(periods, limit=parsed.get("count", 5))

    if intent == "LATE":
        return late_response(predict_next_period(lengths, last_start), date.today())

    return unknown_response()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply to any text message."""
    user_id = db.get_or_create_user("Ash")
    reply = build_reply(update.message.text, user_id)
    await update.message.reply_text(reply)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start — greet and capture the chat id."""
    chat_id = update.effective_chat.id
    print(f"Your chat id is: {chat_id}")  # copy this into .env
    await update.message.reply_text(
        "Cycle Companion here. Ask me when your next period is, "
        "say 'status' or 'stats', or tell me when it starts/ends."
    )


def main():
    token = os.environ["TELEGRAM_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
