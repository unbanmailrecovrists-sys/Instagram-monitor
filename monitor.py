import os
import instaloader
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- CONFIG ---
TOKEN = '8689195046:AAEotMhY0k3XRxd-MQ4piCZUTZvRH1sG6RQ'
CHAT_ID = '5590079891'
IG_USER = 'monitor_ig'
IG_PASS = '1q2w3e4r5t'

L = instaloader.Instaloader()
monitored_accounts = set()

# --- LOGIN (Sirf ek baar startup par) ---
try:
    L.login(IG_USER, IG_PASS)
    print("✅ IG Login Successful!")
except Exception as e:
    print(f"⚠️ Login Warning: {e} (Bot checking as guest)")

def get_ig_status(username):
    try:
        # Login ke sath check karega toh accurate aayega
        instaloader.Profile.from_username(L.context, username)
        return "ACTIVE"
    except instaloader.exceptions.ProfileNotExistsException:
        return "BANNED"
    except Exception:
        return "ERROR"

# --- TELEGRAM COMMANDS ---
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        user = context.args[0].replace('@', '').lower()
        status = get_ig_status(user)
        icon = "🟢" if status == "ACTIVE" else "🚨"
        await update.message.reply_text(f"{icon} @{user}: {status}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 IG Monitor Online!\n/add username\n/check username")

def main():
    Thread(target=run).start()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("check", check))
    # Baki commands (add/del) yahan add kar sakte ho
    application.run_polling()

if __name__ == '__main__':
    main()
