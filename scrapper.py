import requests
from bs4 import BeautifulSoup
import time
import os
import threading
from flask import Flask, jsonify

app = Flask(__name__)

# Load API keys from Render's environment variables
API_KEY = os.getenv("SCRAPERAPI_KEY")  # Set this in Render
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Set this in Render
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Set this in Render

# Google Finance URL
TICKER = "BTC-USD"
URL = f"https://www.google.com/finance/quote/{TICKER}"

# Function to Fetch Stock Price
def fetch_stock_price():
    try:
        proxy_url = f"https://api.scraperapi.com?api_key={API_KEY}&url={URL}"
        response = requests.get(proxy_url)
        
        if response.status_code != 200:
            print(f"Error fetching data: {response.status_code}, {response.text}")
            return {"error": "Failed to fetch data from Google Finance"}

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract price
        price_element = soup.find(class_="YMlKec fxKbKc")
        if price_element:
            price = float(price_element.text.replace("₹", "").replace(",", ""))
        else:
            raise ValueError("Price element not found in the HTML response")

        print(f"Current Price: ₹{price}")  # Debugging

        send_telegram_alert(price)

        return {"stock": TICKER, "price": price}

    except Exception as e:
        print(f"Error: {e}")  # Log error in Render logs
        return {"error": str(e)}

# Function to Send Telegram Notification
def send_telegram_alert(price):
    message = f"🚨 Price Drop Alert! {TICKER} is now ₹{price} 🚨"
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}

    response = requests.post(telegram_url, data=payload)
    
    # Debugging: Print response from Telegram API
    print(f"Telegram Response: {response.status_code}, {response.text}")

# API Route to Fetch Stock Price
@app.route('/')
def get_price():
    return jsonify(fetch_stock_price())

# Run Scraper in a Separate Background Thread
def run_scraper():
    while True:
        fetch_stock_price()
        time.sleep(5)  # Fetch price every 5 seconds

# Start background thread
threading.Thread(target=run_scraper, daemon=True).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
