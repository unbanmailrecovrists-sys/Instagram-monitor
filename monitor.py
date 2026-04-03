import discord
from discord.ext import commands, tasks
import cloudscraper
import re
import os
from flask import Flask
from threading import Thread

# ==========================================
# 🌐 RENDER PORT FIX (KEEP ALIVE)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Monitor Bot is Online! Port 8080 Active."

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
TOKEN = os.environ.get('DISCORD_TOKEN')
PROXY = os.environ.get('PROXY_URL') 
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))
INTERVAL_MINS = int(os.environ.get('CHECK_INTERVAL', 25))

# Monitoring List (Yahan usernames dalo)
ACCOUNTS = ["zuck", "croprated", "instagram"]

intents = discord.Intents.default()
intents.message_content = True # 👈 Ye Discord Portal par ON hona chahiye
bot = commands.Bot(command_prefix="!", intents=intents)
scraper = cloudscraper.create_scraper()

# ==========================================
# 🔍 MONITORING LOGIC
# ==========================================
def check_instagram_status(username):
    url = f"https://www.instagram.com/{username}/"
    proxies = {"http": PROXY, "https": PROXY} if PROXY else None
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
    }

    try:
        response = scraper.get(url, headers=headers, proxies=proxies, timeout=20)
        html = response.text

        if response.status_code == 404:
            return "🔴 BANNED (404 Not Found)"

        meta_data = re.search(r'<meta content="(.*?)" name="description"', html)
        if meta_data:
            stats = meta_data.group(1)
            if "Followers" in stats or "Posts" in stats:
                return f"🟢 ACTIVE ({stats})"
        
        if "Page Not Found" in html or "link you followed may be broken" in html:
            return "🔴 BANNED (Broken Link)"

        if response.status_code == 429 or "login" in response.url:
            return "⚠️ RATE LIMITED (Proxy Flagged)"
            
        return "❓ DATA MISSING"
    except Exception as e:
        return f"❌ ERROR ({str(e)})"

# ==========================================
# 🤖 DISCORD COMMANDS
# ==========================================

@bot.command()
async def status(ctx):
    """Bot ka status check karne ke liye"""
    await ctx.send(f"✅ **Monitor is Live!**\nChecking every `{INTERVAL_MINS}` mins.\nProxy: `{'Connected' if PROXY else 'None'}`")

@bot.command()
async def check(ctx, username: str):
    """Kisi bhi user ko turant check karne ke liye: !check username"""
    user_clean = username.replace('@', '')
    await ctx.send(f"🔍 Checking @{user_clean}... Please wait.")
    result = check_instagram_status(user_clean)
    await ctx.send(f"📊 **Result for @{user_clean}:**\n{result}")

@bot.command()
async def list(ctx):
    """Monitoring list dekhne ke liye"""
    names = "\n".join([f"- {a}" for a in ACCOUNTS])
    await ctx.send(f"📋 **Monitoring List:**\n{names}")

# ==========================================
# 🔄 AUTO MONITOR TASK
# ==========================================
@tasks.loop(minutes=25)
async def monitor_loop():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return

    print("🔍 Cycle started...")
    for user in ACCOUNTS:
        status = check_instagram_status(user)
        if "BANNED" in status:
            await channel.send(f"🚨 **ALERT:** @{user} is **BANNED**! \nDetails: `{status}`")

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    keep_alive() # Port 8080 fix
    if not monitor_loop.is_running():
        monitor_loop.change_interval(minutes=INTERVAL_MINS)
        monitor_loop.start()

# ==========================================
# 🚀 RUN
# ==========================================
if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("❌ Missing DISCORD_TOKEN")
