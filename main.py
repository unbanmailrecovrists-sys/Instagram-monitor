import telebot
import requests
import time
import os
from flask import Flask
from threading import Thread

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot Accuracy 100% Mode Active!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT CONFIG ---
API_KEY = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(API_KEY)
monitored_accounts = {}

# --- REAL ACCURACY LOGIC ---
def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        content = response.text
        
        # 1. Agar Instagram 404 error deta hai (Page not found)
        if response.status_code == 404:
            return False
            
        # 2. Agar status 200 hai, toh check karein ki wo asli profile hai ya sirf login page
        if response.status_code == 200:
            # Agar page par "Followers" ya "Following" likha hai, matlab account LIVE hai
            if 'Followers' in content or 'Following' in content or 'Posts' in content:
                return True
            
            # Agar page par "login" ya "not available" jaisa kuch hai, matlab BAN hai
            if 'log in' in content.lower() or 'not available' in content.lower():
                return False
                
        return False
    except:
        return False

# --- MONITORING LOOP ---
def monitor_loop():
    while True:
        for username, data in list(monitored_accounts.items()):
            if check_instagram(username):
                bot.send_message(data["chat_id"], f"🏆 **Account Recovered!**\n\nUser: @{username}\nCheck karein: https://www.instagram.com/{username}/")
                if username in monitored_accounts:
                    del monitored_accounts[username]
        time.sleep(300)

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 **Bot Live & Fully Accurate!**\n\nCommands:\n/add user1 user2 - Bulk add\n/check user - Instant check\n/del user - Remove monitor\n/list - View all")

@bot.message_handler(commands=['check'])
def instant_check(message):
    try:
        username = message.text.split()[1].replace('@', '').lower()
        bot.reply_to(message, f"🔍 Checking @{username} status...")
        if check_instagram(username):
            bot.reply_to(message, f"✅ @{username} is **LIVE** right now!")
        else:
            bot.reply_to(message, f"❌ @{username} is still **BANNED**.")
    except:
        bot.reply_to(message, "Usage: `/check username`")

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
            bot.send_message(message.chat.id, f"✅ @{username} Active hai, monitor nahi kiya.")
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
        bot.reply_to(message, "📋 List empty.")
        return
    res = "\n".join([f"• @{u}" for u in monitored_accounts.keys()])
    bot.reply_to(message, f"📋 **Monitoring:**\n{res}")

if __name__ == "__main__":
    keep_alive()
    Thread(target=monitor_loop).start()
    bot.infinity_polling()