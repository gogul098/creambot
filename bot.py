import os
import requests
from bs4 import BeautifulSoup
import time
from dotenv import load_dotenv

# --- CONFIGURATION ---
# WHY: We load environment variables so your credentials stay off the internet.
load_dotenv()
URL = "https://haapysecrets.com/products/the-secret-glutathione-skin-brightening-cream"
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN") 
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")     

def fetch_page():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status() 
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None

def check_stock(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    cart_button = soup.select_one('buy-buttons button[type="submit"]')
    
    if not cart_button:
        print("Error: Target button missing from DOM.")
        return None # Returning None indicates a structural failure, not just out of stock.
        
    if "SOLD OUT" in cart_button.get_text().upper():
        return False
    else:
        return True

def send_telegram_message(message_text):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text
    }
    try:
        response = requests.post(api_url, json=payload)
        
        # THE FIX: We are now checking the HTTP status code. 
        # 200 means OK. Anything else means Telegram rejected your payload.
        if response.status_code != 200:
            print(f"API REJECTED PAYLOAD! HTTP Status: {response.status_code}")
            print(f"Telegram Server Error Response: {response.text}")
            
    except Exception as e:
        print(f"Failed to push message. Network fault: {e}")

def main():
    print("Checking stock...")

    html = fetch_page()

    if html:
        in_stock = check_stock(html)

        if in_stock:
            alert = f"🚨 RESTOCK ALERT! {URL}"
            print(alert)
            send_telegram_message(alert)

        elif in_stock is False:
            print("Still sold out.")

        else:
            send_telegram_message("⚠️ DOM structure changed.")

    else:
        send_telegram_message("⚠️ Failed to fetch website.")
if __name__ == "__main__":
    main()
