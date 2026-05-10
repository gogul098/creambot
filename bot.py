import os
import json
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

URL = "https://haapysecrets.com/products/the-secret-glutathione-skin-brightening-cream"

TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")

STATE_FILE = "state.json"

# Send sold-out reminder only every 5 hours
REMINDER_INTERVAL = 60


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    return {
        "last_reminder": 0,
        "last_stock_status": "unknown"
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def fetch_page():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None


def check_stock(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    cart_button = soup.select_one('buy-buttons button[type="submit"]')

    if not cart_button:
        print("Button not found.")
        return None

    button_text = cart_button.get_text(strip=True).upper()

    sold_out_keywords = [
        "SOLD OUT",
        "OUT OF STOCK",
        "UNAVAILABLE"
    ]

    if any(word in button_text for word in sold_out_keywords):
        return False

    return True


def send_telegram_message(message_text):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text
    }

    try:
        response = requests.post(api_url, json=payload)

        if response.status_code != 200:
            print(f"Telegram error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Telegram send failed: {e}")


def main():
    print("Checking stock...")

    state = load_state()

    current_time = time.time()

    html = fetch_page()

    if not html:
        send_telegram_message("⚠️ Failed to fetch website.")
        return

    in_stock = check_stock(html)

    if in_stock is True:

        # Only alert once when stock changes
        if state["last_stock_status"] != "in_stock":
            alert = f"🚨 RESTOCK ALERT!\n\nBuy now:\n{URL}"

            print(alert)

            send_telegram_message(alert)

            state["last_stock_status"] = "in_stock"

    elif in_stock is False:

        print("Still sold out.")

        # Send reminder every 5 hours
        if current_time - state["last_reminder"] > REMINDER_INTERVAL:

            reminder = (
                "⏳ Product still sold out.\n\n"
                f"Last checked: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            send_telegram_message(reminder)

            state["last_reminder"] = current_time

        state["last_stock_status"] = "sold_out"

    else:
        send_telegram_message("⚠️ DOM structure changed.")

    save_state(state)


if __name__ == "__main__":
    main()
