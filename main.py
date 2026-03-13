import telebot
import requests
import time
import os
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Final Accuracy 4.0 - Meta Check Active!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

API_KEY = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(API_KEY)
monitored_accounts = {}

def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        content = response.text
        
        # LOGIC: Instagram ke metadata title ko check karein
        # Active profile ka title aisa hota hai: "Name (@username) • Instagram photos and videos"
        # Banned/Login page ka title sirf "Instagram" ya "Login" hota hai
        
        if response.status_code == 200:
            # Agar title mein "@username" aur "Instagram" dono hain, toh account 100% LIVE hai
            if f"@{username}" in content and "Instagram" in content:
                # Double check: Page par "Followers" ya "Posts" ka mention hona chahiye
                if 'Followers' in content or 'Posts' in content or 'Following' in content:
                    return True
        
        return False
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 **Accuracy Fix 4.0 Live!**\n\nAb bot dhoka nahi khayega.\n/add - Bulk Add\n/check - Instant Check\n/list - View list")

@bot.message_handler(commands=['check'])
def instant_check(message):
    try:
        username = message.text.split()[1].replace('@', '').lower()
        bot.reply_to(message, f"🔍 Validating @{username}...")
        if check_instagram(username):
            bot.reply_to(message, f"✅ @{username} is **LIVE**!")
        else:
            bot.reply_to(message, f"❌ @{username} is **BANNED**.")
    except:
        bot.reply_to(message, "Usage: /check username")

@bot.message_handler(commands=['add'])
def add_bulk(message):
    args = message.text.split()[1:]
    for username in args:
        username = username.replace('@', '').lower()
        bot.send_message(message.chat.id, f"🔍 Checking @{username}...")
        if check_instagram(username):
            bot.send_message(message.chat.id, f"✅ @{username} already Live. Skipping!")
        else:
            monitored_accounts[username] = {"chat_id": message.chat.id}
            bot.send_message(message.chat.id, f"🚀 @{username} added to monitor.")

@bot.message_handler(commands=['del'])
def delete_acc(message):
    try:
        u = message.text.split()[1].replace('@', '').lower()
        if u in monitored_accounts:
            del monitored_accounts[u]
            bot.reply_to(message, f"🗑️ Removed @{u}")
        else:
            bot.reply_to(message, "❌ Not in list.")
    except: pass

@bot.message_handler(commands=['list'])
def list_acc(message):
    if not monitored_accounts:
        bot.reply_to(message, "📋 List is empty.")
        return
    res = "\n".join([f"• @{u}" for u in monitored_accounts.keys()])
    bot.reply_to(message, f"📋 **Monitoring:**\n{res}")

def monitor_loop():
    while True:
        for username, data in list(monitored_accounts.items()):
            if check_instagram(username):
                bot.send_message(data["chat_id"], f"🏆 **Account Recovered!**\n\nUser: @{username}")
                if username in monitored_accounts:
                    del monitored_accounts[username]
        time.sleep(300)

if __name__ == "__main__":
    keep_alive()
    Thread(target=monitor_loop).start()
    bot.infinity_polling()