import json
import os
from datetime import date, datetime
from pathlib import Path

import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

PROGRAM_START_DATE = os.getenv("PROGRAM_START_DATE", "")  # YYYY-MM-DD, optional
STATE_FILE = Path(os.getenv("STATE_FILE", "progress_state.json"))
PROGRAM_FILE = Path(os.getenv("PROGRAM_FILE", "program_28_days.json"))
TIMEZONE_NOTE = os.getenv("TIMEZONE_NOTE", "Mountain Time")


def load_program():
    with PROGRAM_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if STATE_FILE.exists():
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_day_sent": 0, "last_sent_date": ""}


def save_state(state):
    with STATE_FILE.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def day_from_start_date():
    if not PROGRAM_START_DATE:
        return None
    start = date.fromisoformat(PROGRAM_START_DATE)
    today = date.today()
    delta = (today - start).days + 1
    if delta < 1:
        return 1
    if delta > 28:
        return 28
    return delta


def next_day_from_state(state):
    today_str = date.today().isoformat()
    if state.get("last_sent_date") == today_str:
        return None
    last_day = int(state.get("last_day_sent", 0))
    return min(last_day + 1, 28)


def format_message(item):
    return f"""🧹 28-Day Japanese Reset — Day {item['day']}

Theme: {item['theme']}

Today’s task:
{item['task']}

Rule:
{item['rule']}

Why this works:
{item['why']}

Time required: {item['time_required']}

Tonight’s check-in:
{item['check_in']}

Reply DONE when finished."""


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=30)
    response.raise_for_status()
    return response.json()


def main():
    program = load_program()
    state = load_state()

    fixed_day = day_from_start_date()
    if fixed_day is not None:
        day_number = fixed_day
    else:
        day_number = next_day_from_state(state)

    if day_number is None:
        print("Already sent today's message.")
        return

    item = program[day_number - 1]
    message = format_message(item)
    send_telegram(message)

    state["last_day_sent"] = day_number
    state["last_sent_date"] = date.today().isoformat()
    state["last_sent_at"] = datetime.now().isoformat(timespec="seconds")
    state["timezone_note"] = TIMEZONE_NOTE
    save_state(state)

    print(f"Sent day {day_number}.")


if __name__ == "__main__":
    main()
