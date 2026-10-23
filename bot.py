"""Cycle Companion — Telegram bot. Answers you AND sends the daily reminder."""
import os
from datetime import date, datetime
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

# File that records the last date a reminder was sent,
# so we don't spam you multiple times a day.
LAST_REMINDER_FILE = "last_reminder.txt"


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


def reminder_due(prediction, periods, today):
    """Which reminder (if any) fires today."""
    window_start = prediction["window_start"]
    window_end = prediction["window_end"]

    if periods:
        last_start = date.fromisoformat(periods[-1]["start_date"])
        if (today - last_start).days < 21:
            return None  # period happened recently, no reminder

    if window_start <= today <= window_end:
        return ("You're in your predicted window and I haven't seen a log. "
                "Period started, or are we playing hide and seek?")

    if today > window_end:
        return ("You're past your window end and nothing's logged. "
                "Either it came and you forgot, or it's genuinely late — "
                "tell me which.")

    days_to_window = (window_start - today).days
    if 1 <= days_to_window <= 3:
        return ("Heads up — your period window opens in a few days. "
                "Log it when it starts so I can keep your stats honest.")

    return None


def phase_alert(cycle_day):
    """Alert when a phase is approaching."""
    if cycle_day == 8:
        return ("Fertile window coming up around now — you may notice "
                "clear, stretchy discharge. Just so you're not surprised.")
    return None


def already_sent_today():
    """True if we already sent a reminder today."""
    try:
        with open(LAST_REMINDER_FILE) as f:
            return f.read().strip() == str(date.today())
    except FileNotFoundError:
        return False


def mark_sent_today():
    """Record that we sent a reminder today."""
    with open(LAST_REMINDER_FILE, "w") as f:
        f.write(str(date.today()))


async def maybe_send_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Send the 9 AM reminder if it's due and not already sent today."""
    now = datetime.now()
    if now.hour < 9:
        return  # too early

    if already_sent_today():
        return  # already reminded today

    user_id = db.get_or_create_user("Ash")
    periods = db.get_periods(user_id)
    if not periods:
        return

    lengths = calculate_cycle_lengths(periods)
    stats = calculate_statistics(lengths)
    last_start = date.fromisoformat(periods[-1]["start_date"])
    today = date.today()
    prediction = predict_next_period(lengths, last_start)
    cycle_day = (today - last_start).days + 1

    message = reminder_due(prediction, periods, today)
    if not message:
        message = phase_alert(cycle_day)

    if message:
        await context.bot.send_message(chat_id=os.environ["MY_CHAT_ID"], text=message)
        mark_sent_today()
        print(f"Sent reminder: {message}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply to any text message, and check if a reminder is due."""
    user_id = db.get_or_create_user("Ash")
    reply = build_reply(update.message.text, user_id)
    await update.message.reply_text(reply)

    # Every message is a chance to check the clock.
    await maybe_send_daily_reminder(context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greet and trigger the daily reminder check."""
    chat_id = update.effective_chat.id
    print(f"Your chat id is: {chat_id}")
    await update.message.reply_text(
        "Cycle Companion here. Ask me when your next period is, "
        "say 'status' or 'stats', or tell me when it starts/ends."
    )
    await maybe_send_daily_reminder(context)


def main():
    token = os.environ["TELEGRAM_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
