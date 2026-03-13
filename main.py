import telebot
import requests
import time
import os
from flask import Flask
from threading import Thread

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online with /check command!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT CONFIG ---
API_KEY = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(API_KEY)
monitored_accounts = {}

# --- ACCURATE CHECKING LOGIC ---
def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    # Google Bot headers to bypass block
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
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
    bot.reply_to(message, "✅ **Bot Active!**\n\nCommands:\n/add user1 user2 - Bulk add\n/check user - Instant check\n/del user - Remove monitor\n/list - View list")

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
            bot.send_message(message.chat.id, f"✅ @{username} Active hai, skip kar raha hoon.")
        else:
            monitored_accounts[username] = {"chat_id": message.chat.id}
            bot.send_message(message.chat.id, f"🚀 @{username} added to monitor list.")

@bot.message_handler(commands=['del'])
def delete_acc(message):
    try:
        u = message.text.split()[1].replace('@', '').lower()
        if u in monitored_accounts:
            del monitored_accounts[u]
            bot.reply_to(message, f"🗑️ @{u} removed from list.")
        else:
            bot.reply_to(message, "❌ Not in list.")
    except:
        bot.reply_to(message, "Usage: `/del user`")

@bot.message_handler(commands=['list'])
def list_acc(message):
    if not monitored_accounts:
        bot.reply_to(message, "📋 List khali hai.")
        return
    res = "\n".join([f"• @{u}" for u in monitored_accounts.keys()])
    bot.reply_to(message, f"📋 **Current Monitoring:**\n{res}")

if __name__ == "__main__":
    keep_alive()
    Thread(target=monitor_loop).start()
    bot.infinity_polling()