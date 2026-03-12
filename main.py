import telebot
import requests
import time
import os
from flask import Flask
from threading import Thread

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"

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
    # Strong headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # We use a session to handle cookies if needed
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=20)
        content = response.text
        
        # Check 1: Agar page par "login" ya "password" bahut zyada hai, toh wo profile nahi hai
        if "Login" in content and "Password" in content and "signup" in content:
            return False # Ye sirf login screen hai, profile nahi
            
        # Check 2: Asli profile par 'Followers' ya 'biography' ka data hota hai
        if response.status_code == 200:
            if 'Follower' in content or 'Following' in content or 'logging_page_id' not in content:
                # Agar "logging_page_id" content mein nahi hai, matlab ye login page nahi hai
                return True
        
        return False
    except:
        return False

def monitor_loop():
    while True:
        for username, data in list(monitored_accounts.items()):
            if check_instagram(username):
                bot.send_message(data["chat_id"], f"🏆 **Account Recovered!**\n\nUser: @{username}\nLink: https://www.instagram.com/{username}/")
                del monitored_accounts[username]
        time.sleep(300)

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot Active! Use `/add username` to monitor.")

@bot.message_handler(commands=['add'])
def add_account(message):
    try:
        username = message.text.split()[1].replace('@', '')
        bot.reply_to(message, f"🔍 Checking @{username}...")
        
        is_live = check_instagram(username)
        
        if is_live:
            bot.reply_to(message, f"✅ @{username} Live hai!")
        else:
            monitored_accounts[username] = {"chat_id": message.chat.id}
            bot.reply_to(message, f"🚀 Monitoring started for @{username}.")
    except:
        bot.reply_to(message, "Usage: `/add username`")

if __name__ == "__main__":
    keep_alive()
    Thread(target=monitor_loop).start()
    bot.infinity_polling()