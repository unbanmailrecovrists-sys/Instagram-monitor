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
def home(): return "Monitor Bot is Online!"

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
PROXY_RAW = os.environ.get('PROXY_URL')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))
INTERVAL_MINS = int(os.environ.get('CHECK_INTERVAL', 25))

# Default Monitoring List
ACCOUNTS = {"zuck", "instagram"} 

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)
scraper = cloudscraper.create_scraper()

def get_clean_proxies():
    if not PROXY_RAW: return None
    url = PROXY_RAW.strip().replace('"', '').replace("'", "").replace(" ", "")
    return {"http": url, "https": url}

def check_instagram_status(username):
    url = f"https://www.instagram.com/{username}/"
    proxies = get_clean_proxies()
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"}
    try:
        response = scraper.get(url, headers=headers, proxies=proxies, timeout=20)
        if response.status_code == 404: return "🔴 BANNED (404)"
        meta = re.search(r'<meta content="(.*?)" name="description"', response.text)
        if meta:
            stats = meta.group(1)
            if "Followers" in stats or "Posts" in stats: return f"🟢 ACTIVE ({stats})"
        if "Page Not Found" in response.text: return "🔴 BANNED (Broken Link)"
        return "⚠️ RATE LIMITED/LOGIN WALL"
    except Exception: return "❌ PROXY/CONNECTION ERROR"

# ==========================================
# 🤖 DISCORD COMMANDS (ADD / REMOVE / LIST)
# ==========================================

@bot.command()
async def add(ctx, username: str):
    """Monitor list mein account add karne ke liye: !add zuck"""
    user = username.replace('@', '').lower()
    ACCOUNTS.add(user)
    await ctx.send(f"✅ **@{user}** ko monitoring list mein add kar diya gaya hai.")

@bot.command()
async def remove(ctx, username: str):
    """Monitor list se account hatane ke liye: !remove zuck"""
    user = username.replace('@', '').lower()
    if user in ACCOUNTS:
        ACCOUNTS.remove(user)
        await ctx.send(f"🗑️ **@{user}** ko list se hata diya gaya hai.")
    else:
        await ctx.send(f"❌ **@{user}** list mein nahi hai.")

@bot.command()
async def list(ctx):
    """Saare monitored accounts dekhne ke liye"""
    if not ACCOUNTS:
        await ctx.send("📋 Monitoring list khali hai.")
        return
    names = "\n".join([f"- {a}" for a in ACCOUNTS])
    await ctx.send(f"📋 **Monitored Accounts:**\n{names}")

@bot.command()
async def check(ctx, username: str):
    """Turant check karne ke liye"""
    user = username.replace('@', '')
    await ctx.send(f"🔍 Checking @{user}...")
    res = check_instagram_status(user)
    await ctx.send(f"📊 **Result:** {res}")

@bot.command()
async def status(ctx):
    await ctx.send(f"✅ **Monitor Active**\nInterval: `{INTERVAL_MINS}m` | Accounts: `{len(ACCOUNTS)}`")

# ==========================================
# 🔄 AUTO MONITOR TASK
# ==========================================
@tasks.loop(minutes=25)
async def monitor_loop():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel or not ACCOUNTS: return
    for user in list(ACCOUNTS): # list() use kiya taaki loop ke beech mein size change na ho
        status = check_instagram_status(user)
        if "BANNED" in status:
            await channel.send(f"🚨 **ALERT:** @{user} is **BANNED**! \nDetails: `{status}`")

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    if not monitor_loop.is_running():
        monitor_loop.change_interval(minutes=INTERVAL_MINS)
        monitor_loop.start()

# ==========================================
# 🚀 EXECUTION START (Render Port Fix)
# ==========================================
if __name__ == "__main__":
    keep_alive() # Flask starts first for Render
    if TOKEN:
        bot.run(TOKEN)
