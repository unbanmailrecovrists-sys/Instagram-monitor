import telebot
import requests
import time
import os
import random
from flask import Flask
from threading import Thread

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online - High Accuracy Mode!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT CONFIG ---
API_KEY = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(API_KEY)
monitored_accounts = {}

# --- USER AGENTS LIST ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

# --- ACCURATE CHECKING LOGIC ---
def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
    }
    
    try:
        # Using a fresh session for every check to clear cookies
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        content = response.text
        
        # Error 404 means the user is 100% not found (Banned or Deleted)
        if response.status_code == 404:
            return False
            
        # Logic 1: Check for Profile Data in JSON/Script (Most Accurate)
        # Active profile has 'biography' or 'edge_followed_by' in the source code
        if 'biography' in content or 'edge_followed_by' in content or '"show_suggested_profiles":true' in content:
            return True
            
        # Logic 2: Detection of Login Wall (Login form means profile is not visible/active)
        if 'login_page' in content or 'Password' in content or 'logging_page_id' in content:
            return False # Profile invisible/Banned
            
        # Logic 3: Fallback check for "Followers" text
        if response.status_code == 200 and 'Follower' in content:
            return True
            
        return False
    except:
        return False

# --- MONITORING LOOP ---
def monitor_loop():
    while True:
        for username, data in list(monitored_accounts.items()):
            if check_instagram(username):
                bot.send_message(data["chat_id"], f"🏆 **Account Recovered!**\n\nUser: @{username}\nLink: https://www.instagram.com/{username}/")
                if username in monitored_accounts:
                    del monitored_accounts[username]
        time.sleep(300)

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ **Bot Online!**\n\nCommands:\n/add user1 user2 - Bulk add\n/del user - Remove\n/list - See active monitors")

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
            bot.send_message(message.chat.id, f"✅ @{username} Active hai, Skip kar raha hoon.")
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
    except:
        bot.reply_to(message, "Usage: `/del user`")

@bot.message_handler(commands=['list'])
def list_acc(message):
    if not monitored_accounts:
        bot.reply_to(message, "List khali hai.")
        return
    res = "\n".join([f"• @{u}" for u in monitored_accounts.keys()])
    bot.reply_to(message, f"📋 **Monitoring:**\n{res}")

if __name__ == "__main__":
    keep_alive()
    Thread(target=monitor_loop).start()
    bot.infinity_polling()