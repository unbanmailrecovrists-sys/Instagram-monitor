import telebot
import requests
import time
import os
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Accuracy Fix 3.0 is Live!"

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
        
        # AGAR STATUS 200 HAI, TOH BHI CHECK KAREIN KI ASLI PROFILE HAI YA NAHI
        if response.status_code == 200:
            # 1. Login Page check (Agar page par 'log in' aur 'signup' dono hain, toh ye profile nahi hai)
            if 'log in' in content.lower() and 'signup' in content.lower():
                return False 
            
            # 2. Banned/Unavailable check
            if 'not available' in content.lower() or 'link you followed may be broken' in content.lower():
                return False
            
            # 3. Success Check (Asli profile par ye words zaroor hote hain)
            if 'Followers' in content or 'Following' in content or 'Posts' in content or 'biography' in content:
                return True
                
        return False
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 **Accuracy Fixed!**\nUse /add or /check.")

@bot.message_handler(commands=['check'])
def instant_check(message):
    try:
        username = message.text.split()[1].replace('@', '').lower()
        bot.reply_to(message, f"🔍 Checking @{username}...")
        if check_instagram(username):
            bot.reply_to(message, f"✅ @{username} is **LIVE** (Visible)!")
        else:
            bot.reply_to(message, f"❌ @{username} is **BANNED** (Not visible).")
    except:
        bot.reply_to(message, "Usage: /check username")

@bot.message_handler(commands=['add'])
def add_bulk(message):
    args = message.text.split()[1:]
    for username in args:
        username = username.replace('@', '').lower()
        bot.send_message(message.chat.id, f"🔍 Validating @{username}...")
        if check_instagram(username):
            bot.send_message(message.chat.id, f"✅ @{username} Active hai, skip!")
        else:
            monitored_accounts[username] = {"chat_id": message.chat.id}
            bot.send_message(message.chat.id, f"🚀 @{username} added to monitor list.")

@bot.message_handler(commands=['del'])
def delete_acc(message):
    try:
        u = message.text.split()[1].replace('@', '').lower()
        if u in monitored_accounts:
            del monitored_accounts[u]
            bot.reply_to(message, f"🗑️ @{u} removed.")
        else:
            bot.reply_to(message, "❌ Not in list.")
    except: pass

@bot.message_handler(commands=['list'])
def list_acc(message):
    if not monitored_accounts:
        bot.reply_to(message, "List khali hai.")
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