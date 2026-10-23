"""Daily scheduler — sends proactive reminders via Telegram."""
import os
import asyncio
from datetime import date
from dotenv import load_dotenv
from telegram import Bot

from database import database as db
from cycle.calculator import calculate_cycle_lengths
from cycle.statistics import calculate_statistics
from cycle.predictor import predict_next_period

load_dotenv()

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["MY_CHAT_ID"]


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


async def main():
    db.init_db()
    user_id = db.get_or_create_user("Ash")
    periods = db.get_periods(user_id)
    lengths = calculate_cycle_lengths(periods)
    stats = calculate_statistics(lengths)
    last_start = date.fromisoformat(periods[-1]["start_date"]) if periods else None

    today = date.today()
    prediction = predict_next_period(lengths, last_start)
    cycle_day = (today - last_start).days + 1 if last_start else None

    message = reminder_due(prediction, periods, today)
    if not message and cycle_day:
        message = phase_alert(cycle_day)

    if message:
        bot = Bot(token=TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=message)
        print(f"Sent: {message}")
    else:
        print("No reminder due today.")


if __name__ == "__main__":
    asyncio.run(main())
