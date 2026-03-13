import telebot
import requests
import time
import os
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "API Check Mode Active!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

API_KEY = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(API_KEY)
monitored_accounts = {}

def check_instagram(username):
    # Instagram oEmbed API - Ye sirf live accounts ka data deti hai
    url = f"https://www.instagram.com/p/invalid_post_just_checking_user/?__a=1&__d=dis" 
    profile_url = f"https://www.instagram.com/{username}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    try:
        # Method: Hum profile page ko check karenge par simple tarike se
        response = requests.get(profile_url, headers=headers, timeout=15)
        
        # Agar profile live hai, toh title mein hamesha 'Instagram' se pehle Name ya Username hoga
        # Banned page ka title sirf 'Instagram' hota hai ya 404
        if response.status_code == 200:
            content = response.text
            if f"@{username}" in content or 'Followers' in content:
                return True
            # Ek aakhri check: Agar 200 hai aur page bada hai (Login page), toh hum usey Live hi maanenge
            if len(content) > 10000: 
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
        if check_instagram(username):
            bot.send_message(message.chat.id, f"✅ @{username} Active hai.")
        else:
            monitored_accounts[username] = {"chat_id": message.chat.id}
            bot.send_message(message.chat.id, f"🚀 @{username} added to monitor.")

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