import requests
from bs4 import BeautifulSoup
import time
import os
from flask import Flask, jsonify

app = Flask(__name__)

# Load API Keys from Environment Variables
API_KEY = os.getenv("SCRAPERAPI_KEY")  # ScraperAPI Key
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Telegram Bot Token
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Your Telegram Chat ID

# Google Finance URL
TICKER = "KOTAKBANK:NSE"
URL = f"https://www.google.com/finance/quote/{TICKER}"

# Store the last fetched price
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

        # Store the price for calculations
        last_price = price

        # Check condition and send Telegram alert
        check_condition(price)

        return {"stock": TICKER, "price": price}

    except Exception as e:
        return {"error": str(e)}

# Function to Send Telegram Alert
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, json=payload)

# Function to Check Condition and Send Alert
def check_condition(price):
    threshold = 2000  # Set your target price
    if price > threshold:
        send_telegram_message(f"🚀 Stock Alert: {TICKER} is now ₹{price} (Above ₹{threshold})")

@app.route('/')
def get_price():
    return jsonify(fetch_stock_price())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
