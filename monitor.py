import os
import cloudscraper
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- WEB SERVER FOR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# --- CONFIG ---
TOKEN = 'APNA_TELEGRAM_TOKEN'
CHAT_ID = 'APNA_CHAT_ID'

monitored_accounts = set()
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})

def get_ig_status(username):
    try:
        url = f"https://www.instagram.com/{username}/"
        response = scraper.get(url, timeout=15)
        content = response.text.lower()
        if response.status_code == 404 or "broken link" in content or "content isn't available" in content:
            return "BANNED"
        return "ACTIVE"
    except:
        return "ERROR"

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 IG Monitor Bot Online!\n\n/add username - List mein daalein\n/check username - Turant check karein\n/list - Saari list dekhein\n/del username - List se hatayein")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != CHAT_ID: return
    if context.args:
        user = context.args[0].replace('@', '').lower()
        monitored_accounts.add(user)
        await update.message.reply_text(f"✅ @{user} ko monitoring list mein add kar diya gaya hai.")
    else:
        await update.message.reply_text("Sahi tarika: `/add username`")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != CHAT_ID: return
    if context.args:
        user = context.args[0].replace('@', '').lower()
        status = get_ig_status(user)
        icon = "🟢" if status == "ACTIVE" else "🚨"
        await update.message.reply_text(f"{icon} @{user}: {status}")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != CHAT_ID: return
    user = context.args[0].lower()
    if user in monitored_accounts:
        monitored_accounts.remove(user)
        await update.message.reply_text(f"🗑️ @{user} removed.")

async def list_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not monitored_accounts:
        await update.message.reply_text("List khali hai.")
    else:
        await update.message.reply_text(f"📋 Tracking: {', '.join(monitored_accounts)}")

# --- AUTO CHECK EVERY 10 MIN ---
async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    for user in list(monitored_accounts):
        if get_ig_status(user) == "BANNED":
            await context.bot.send_message(chat_id=CHAT_ID, text=f"🚨 ALERT: @{user} BAN HO GAYA!")
            monitored_accounts.remove(user)

def main():
    Thread(target=run).start()
    app_tg = Application.builder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("add", add))
    app_tg.add_handler(CommandHandler("check", check))
    app_tg.add_handler(CommandHandler("del", delete))
    app_tg.add_handler(CommandHandler("list", list_all))
    
    if app_tg.job_queue:
        app_tg.job_queue.run_repeating(auto_check, interval=600, first=10)
    
    app_tg.run_polling()

if __name__ == '__main__':
    main()