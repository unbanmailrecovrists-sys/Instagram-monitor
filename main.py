import telebot
import requests
import time
import os
import random
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot Accuracy 5.0 - Ultra Mode Live!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

API_KEY = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(API_KEY)
monitored_accounts = {}

def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    
    # List of different User-Agents to confuse Instagram
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    ]

    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    try:
        # Session use karne se cookies manage hoti hain
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        content = response.text
        
        # LOGIC: Agar status 200 hai
        if response.status_code == 200:
            # Agar page ke andar "Followers" ya "@username" ya "Instagram" metadata hai
            if f"@{username}" in content or 'Followers' in content or 'Posts' in content:
                return True
            # Agar login wall aayi hai (mmatlab block ho raha hai), toh hum usey 'Banned' nahi bolenge, 
            # balki try karenge ki wo 'live' hai ya nahi check kare
            if 'logging_page_id' in content:
                # Login wall aksar active accounts par aati hai bots ke liye
                return True 
                
        return False
    except:
        return False

@bot.message_handler(commands=['check'])
def instant_check(message):
    try:
        username = message.text.split()[1].replace('@', '').lower()
        bot.reply_to(message, f"🔍 Checking @{username}...")
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
        bot.send_message(message.chat.id, f"🔍 Validating @{username}...")
        if check_instagram(username):
            bot.send_message(message.chat.id, f"✅ @{username} Active hai. Skip!")
        else:
            monitored_accounts[username] = {"chat_id": message.chat.id}
            bot.send_message(message.chat.id, f"🚀 @{username} Added to monitor list.")

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