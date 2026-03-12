import telebot
import requests
import time
import os
from flask import Flask
from threading import Thread

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online with Delete Command!"

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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        content = response.text
        
        if "Login" in content and "Password" in content:
            return False 
            
        if response.status_code == 200:
            if 'Follower' in content or 'Posts' in content:
                return True
        return False
    except:
        return False

# --- MONITORING LOOP ---
def monitor_loop():
    while True:
        # Copy list to avoid error during iteration
        for username, data in list(monitored_accounts.items()):
            if check_instagram(username):
                bot.send_message(data["chat_id"], f"🏆 **Account Recovered!**\n\nUser: @{username}\nLink: https://www.instagram.com/{username}/")
                if username in monitored_accounts:
                    del monitored_accounts[username]
        time.sleep(300)

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot Active!\n/add - Monitor add karein\n/del - Monitor hatayein\n/list - List dekhein")

@bot.message_handler(commands=['add'])
def add_account(message):
    try:
        username = message.text.split()[1].replace('@', '').lower()
        bot.reply_to(message, f"🔍 Checking @{username}...")
        if check_instagram(username):
            bot.reply_to(message, f"✅ @{username} pehle se Live hai!")
        else:
            monitored_accounts[username] = {"chat_id": message.chat.id}
            bot.reply_to(message, f"🚀 Monitoring started for @{username}")
    except:
        bot.reply_to(message, "Usage: `/add username`")

@bot.message_handler(commands=['del'])
def delete_account(message):
    try:
        username = message.text.split()[1].replace('@', '').lower()
        if username in monitored_accounts:
            del monitored_accounts[username]
            bot.reply_to(message, f"🗑️ @{username} ko monitor list se hata diya gaya hai.")
        else:
            bot.reply_to(message, f"❌ @{username} list mein nahi mila.")
    except:
        bot.reply_to(message, "Usage: `/del username` (Example: /del instagram)")

@bot.message_handler(commands=['list'])
def list_accounts(message):
    if not monitored_accounts:
        bot.reply_to(message, "📋 Abhi koi account monitor nahi ho raha.")
        return
    res = "\n".join([f"• @{u}" for u in monitored_accounts.keys()])
    bot.reply_to(message, f"📋 Current Monitoring List:\n{res}")

# --- START ---
if __name__ == "__main__":
    keep_alive()
    Thread(target=monitor_loop).start()
    bot.infinity_polling()