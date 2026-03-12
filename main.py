import telebot
import requests
import time
import os
from flask import Flask
from threading import Thread

# --- WEB SERVER ---
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

# --- MONITORING LOGIC ---
def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # Check 1: Status 200 hona chahiye
        # Check 2: Page ke andar "Login" ya "Unavailable" jaisa text nahi hona chahiye
        if response.status_code == 200 and 'Login' not in response.text and 'not available' not in response.text.lower():
            return True
    except:
        pass
    return False

def monitor_loop():
    while True:
        for username, data in list(monitored_accounts.items()):
            if check_instagram(username):
                bot.send_message(data["chat_id"], f"🏆 **Account Recovered!**\n\nUser: @{username}\nCheck karein: https://www.instagram.com/{username}/")
                del monitored_accounts[username]
        time.sleep(300) # 5 minutes gap

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot Active! Use `/add username` to monitor.")

@bot.message_handler(commands=['add'])
def add_account(message):
    try:
        username = message.text.split()[1].replace('@', '')
        # Pehle check karein ki kahin abhi se toh live nahi hai
        bot.reply_to(message, f"🔍 Checking @{username}...")
        if check_instagram(username):
            bot.reply_to(message, "Ye account toh pehle se hi live hai! ✅")
        else:
            monitored_accounts[username] = {"chat_id": message.chat.id}
            bot.reply_to(message, f"✅ Monitoring started for @{username}. Recover hote hi alert mil jayega.")
    except:
        bot.reply_to(message, "Sahi tarika: `/add username`")

if __name__ == "__main__":
    keep_alive()
    Thread(target=monitor_loop).start()
    bot.infinity_polling()