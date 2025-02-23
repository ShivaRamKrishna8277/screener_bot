import requests
from bs4 import BeautifulSoup
import time
import os
from flask import Flask, jsonify

app = Flask(__name__)

# Load API keys from Render's environment variables
API_KEY = os.getenv("SCRAPERAPI_KEY")  # Set this in Render
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set this in Render
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Set this in Render

# Google Finance URL
TICKER = "KOTAKBANK:NSE"
URL = f"https://www.google.com/finance/quote/{TICKER}"

# Store Last Price
last_price = None

# Function to Fetch Stock Price
def fetch_stock_price():
    global last_price
    try:
        proxy_url = f"https://api.scraperapi.com?api_key={API_KEY}&url={URL}"
        response = requests.get(proxy_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        price_class = "YMlKec fxKbKc"
        price = float(soup.find(class_=price_class).text.replace("₹", "").replace(",", ""))

        print(f"Current Price: ₹{price}")  # Debugging

        # Example Condition: If price drops by ₹10, send an alert
        if last_price and price < last_price - 10:
            send_telegram_alert(price)

        last_price = price
        return {"stock": TICKER, "price": price}

    except Exception as e:
        return {"error": str(e)}

# Function to Send Telegram Notification
def send_telegram_alert(price):
    message = f"🚨 Price Drop Alert! {TICKER} is now ₹{price} 🚨"
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(telegram_url, data=payload)

@app.route('/')
def get_price():
    return jsonify(fetch_stock_price())

if __name__ == '__main__':
    while True:
        fetch_stock_price()
        time.sleep(30)  # 2 requests per minute
