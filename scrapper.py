import requests
from bs4 import BeautifulSoup
import time
import os
import threading
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

# Load API keys from Render's environment variables
API_KEY = os.getenv("SCRAPERAPI_KEY")  # Set this in Render
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set this in Render
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Set this in Render

# List of 50 Nifty Stocks
NIFTY_50_TICKERS = [
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "HINDUNILVR", "SBIN",
    "HDFC", "BAJFINANCE", "KOTAKBANK", "LT", "ITC", "BHARTIARTL", "ASIANPAINT",
    "MARUTI", "AXISBANK", "ULTRACEMCO", "WIPRO", "HCLTECH", "TITAN", "SUNPHARMA",
    "TECHM", "NTPC", "POWERGRID", "TATASTEEL", "JSWSTEEL", "NESTLEIND", "DRREDDY",
    "INDUSINDBK", "BAJAJFINSV", "GRASIM", "ADANIPORTS", "COALINDIA", "CIPLA",
    "HINDALCO", "TATAMOTORS", "SBILIFE", "DIVISLAB", "BPCL", "IOC", "BRITANNIA",
    "M&M", "HEROMOTOCO", "UPL", "EICHERMOT", "ONGC", "SHREECEM", "APOLLOHOSP",
    "BAJAJ-AUTO", "TATACONSUM", "VEDL"
]

# Google Finance URL Template
GOOGLE_FINANCE_URL = "https://www.google.com/finance/quote/{}:NSE"

# Store ORB Data
orb_data = {}  # { "RELIANCE": {"high": 2500, "low": 2480, "captured": True}}

# Function to Fetch Stock Price
def fetch_stock_price(ticker):
    try:
        url = GOOGLE_FINANCE_URL.format(ticker)
        proxy_url = f"https://api.scraperapi.com?api_key={API_KEY}&url={url}"
        response = requests.get(proxy_url)
        
        if response.status_code != 200:
            print(f"Error fetching {ticker}: {response.status_code}, {response.text}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        price_element = soup.find(class_="YMlKec fxKbKc")

        if price_element:
            price = float(price_element.text.replace("₹", "").replace(",", ""))
            return price
        else:
            print(f"Price element not found for {ticker}")
            return None
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

# Function to Check ORB Breakout
def check_orb_breakout(ticker, price):
    if ticker in orb_data:
        high = orb_data[ticker]["high"]
        low = orb_data[ticker]["low"]

        if price > high:  # Breakout Above High
            send_telegram_alert(f"🚀 BUY Signal: {ticker} broke above ₹{high}, now ₹{price} 🚀")
        elif price < low:  # Breakout Below Low
            send_telegram_alert(f"🔻 SELL Signal: {ticker} broke below ₹{low}, now ₹{price} 🔻")

# Function to Send Telegram Notification
def send_telegram_alert(message):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(telegram_url, data=payload)
    print(f"Telegram Response: {response.status_code}, {response.text}")

# Background Task to Monitor ORB
def run_orb_strategy():
    while True:
        current_time = datetime.now().strftime("%H:%M:%S")

        for ticker in NIFTY_50_TICKERS:
            price = fetch_stock_price(ticker)
            if price is None:
                continue  # Skip if price couldn't be fetched

            if "09:15:00" <= current_time <= "09:30:00":  # Capture ORB
                if ticker not in orb_data:
                    orb_data[ticker] = {"high": price, "low": price, "captured": False}
                else:
                    orb_data[ticker]["high"] = max(orb_data[ticker]["high"], price)
                    orb_data[ticker]["low"] = min(orb_data[ticker]["low"], price)

            elif current_time > "09:30:00" and ticker in orb_data:  # Check for breakout
                check_orb_breakout(ticker, price)

        time.sleep(10)  # Check every 10 seconds

# API Route to Get ORB Data
@app.route('/')
def get_orb_data():
    return jsonify(orb_data)

# Start Background Thread for ORB Monitoring
threading.Thread(target=run_orb_strategy, daemon=True).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
