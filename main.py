import telebot
import requests
import time
import os
from flask import Flask
from threading import Thread

# --- WEB SERVER FOR 24/7 ---
app = Flask('')
@app.route('/')
def home(): return "Telegram Bot is Live!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT CONFIG ---
API_KEY = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(API_KEY)
monitored_accounts = {}

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot chalu hai! Kisi account ko monitor karne ke liye likhein: /add username")

@bot.message_handler(commands=['add'])
def add_account(message):
    try:
        username = message.text.split()[1].replace('@', '')
        monitored_accounts[username] = {"chat_id": message.chat.id, "time": time.time()}
        bot.reply_to(message, f"✅ Monitoring started for @{username}. Recover hote hi main message bhej dunga.")
    except:
        bot.reply_to(message, "Sahi tarika: `/add username` (e.g., /add instagram)")

@bot.message_handler(commands=['list'])
def list_accounts(message):
    if not monitored_accounts:
        bot.reply_to(message, "List khali hai!")
        return
    res = "\n".join([f"• @{u}" for u in monitored_accounts.keys()])
    bot.reply_to(message, f"📋 Monitored List:\n{res}")

# --- MONITORING LOGIC ---
def monitor():
    while True:
        for username, data in list(monitored_accounts.items()):
            url = f"https://www.instagram.com/{username}/"
            headers = {'User-Agent': 'Mozilla/5.0'}
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    bot.send_message(data["chat_id"], f"🏆 **Account Recovered!**\n\nUser: @{username}\nCheck karein: {url}")
                    del monitored_accounts[username]
            except: pass
        time.sleep(300) # Har 5 min mein check karega

if __name__ == "__main__":
    keep_alive()
    Thread(target=monitor).start()
    bot.infinity_polling()
