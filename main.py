import telebot
import requests
import time
import os
import random
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Accuracy 2.0 is Live!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

API_KEY = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(API_KEY)
monitored_accounts = {}

def check_instagram(username):
    url = f"https://www.instagram.com/{username}/?__a=1&__d=dis" # Mobile API endpoint
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'https://www.instagram.com/{username}/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        content = response.text
        
        # Check 1: Agar Status 404 hai toh confirm ban hai
        if response.status_code == 404:
            return False
            
        # Check 2: Agar Status 200 hai, toh check karein ki ye asli profile data hai ya nahi
        if response.status_code == 200:
            # Asli profile mein "logging_page_id" nahi hota, balki user data hota hai
            if '"logging_page_id":"profilePage_' in content and 'Followers' in content:
                return True
            # Ek aur check: active profile ke source mein 'profile_pic_url' hota hai
            if 'profile_pic_url' in content or 'edge_followed_by' in content:
                return True
                
        return False
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 **Bot Accurate Mode On!**\n\n/add user1 user2 - Bulk\n/del user - Remove\n/list - View List")

@bot.message_handler(commands=['add'])
def add_bulk(message):
    args = message.text.split()[1:]
    if not args:
        bot.reply_to(message, "Usage: `/add user1 user2`")
        return
    
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
            bot.reply_to(message, f"🗑️ @{u} Removed.")
        else:
            bot.reply_to(message, "❌ Not in list.")
    except:
        bot.reply_to(message, "Usage: `/del user`")

@bot.message_handler(commands=['list'])
def list_acc(message):
    if not monitored_accounts:
        bot.reply_to(message, "List empty.")
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