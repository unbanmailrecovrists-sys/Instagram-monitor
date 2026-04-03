import discord
from discord.ext import commands, tasks
import cloudscraper
import re
import os
from flask import Flask
from threading import Thread

# ==========================================
# 🌐 RENDER PORT FIX (SABSE PEHLE)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online!"

def run_flask():
    # Render se port uthayega, default 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# Is function ko sidha execution block mein call karenge
def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True # Taaki main bot ke saath hi band ho
    t.start()

# ==========================================
# ⚙️ CONFIG & BOT SETUP
# ==========================================
TOKEN = os.environ.get('DISCORD_TOKEN')
PROXY = os.environ.get('PROXY_URL')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
scraper = cloudscraper.create_scraper()

# (Monitoring Logic functions wahi purane wale dalo...)

@bot.event
async def on_ready():
    print(f"✅ Discord Bot logged in as {bot.user}")
    if not monitor_loop.is_running():
        monitor_loop.start()

# ... (Tasks aur Commands wala hissa) ...

# ==========================================
# 🚀 EXECUTION START (Dhyan se dekho)
# ==========================================
if __name__ == "__main__":
    print("Starting Flask Server...")
    keep_alive() # 👈 Ye sabse pehle chalega
    
    if TOKEN:
        print("Connecting to Discord...")
        bot.run(TOKEN)
    else:
        print("❌ Error: DISCORD_TOKEN missing!")
