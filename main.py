import telebot
import requests
import time
import os
from flask import Flask
from threading import Thread

# --- WEB SERVER FOR 24/7 ---
app = Flask('')
@app.route('/')
def home(): return "Telegram Bot is Live & Accurate!"

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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        content = response.text
        
        # Check 1: Agar 404 hai toh confirm ban hai
        if response.status_code == 404:
            return False
            
        # Check 2: Agar 200 hai toh check karein ki asli profile hai ya sirf login wall
        if response.status_code == 200:
            # Asli profile par 'Followers' ya 'Posts' likha hota hai
            if 'Followers' in content or 'Posts' in content or 'Following' in content:
                return True
            return False
    except:
        pass
    return False

def monitor_loop():
    while True:
        # List ka copy banate hain taaki loop mein error na aaye
        for username, data in list(monitored_accounts.items()):
            if check_instagram(username):
                bot.send_message(data["chat_id"], f"🏆 **Account Recovered!**\n\nUser: @{username}\nCheck karein: https://www.instagram.com/{username}/")
                del monitored_accounts[username]
        time.sleep(300) # Har 5 minute mein check karega

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot Active! Use `/add username` to monitor an Instagram account.")

@bot.message_handler(commands=['add'])
def add_account(message):
    try:
        username = message.text.split()[1].replace('@', '')
        bot.reply_to(message, f"🔍 Checking @{username} status...")
        
        if check_instagram(username):
            bot.reply_to(message, f"✅ @{username} toh pehle se hi Live hai! Ise monitor karne ki zaroorat nahi.")
        else:
            monitored_accounts[username] = {"chat_id": message.chat.id}
            bot.reply_to(message, f"🚀 Monitoring started for @{username}. Recover hote hi main message bhej dunga.")
    except:
        bot.reply_to(message, "Usage: `/add username` (Example: /add instagram)")

@bot.message_handler(commands=['list'])
def list_accounts(message):
    if not monitored_accounts:
        bot.reply_to(message, "Abhi koi account monitor nahi ho raha.")
        return
    res = "\n".join([f"• @{u}" for u in monitored_accounts.keys()])
    bot.reply_to(message, f"📋 Current Monitoring List:\n{res}")

# --- START BOT ---
if __name__ == "__main__":
    keep_alive()
    Thread(target=monitor_loop).start()
    print("Accurate Telegram Bot Started...")
    bot.infinity_polling()