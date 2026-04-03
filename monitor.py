import discord
from discord.ext import commands, tasks
import cloudscraper
import re
import os
from flask import Flask
from threading import Thread

# --- RENDER PORT FIX ---
app = Flask('')
@app.route('/')
def home(): return "Monitor Live"
def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- CONFIG ---
TOKEN = os.environ.get('DISCORD_TOKEN')
PROXY_RAW = os.environ.get('PROXY_URL')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))
INTERVAL_MINS = int(os.environ.get('CHECK_INTERVAL', 25))

ACCOUNTS = ["zuck", "croprated", "instagram"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
scraper = cloudscraper.create_scraper()

def get_clean_proxies():
    if not PROXY_RAW:
        return None
    # 💡 Ye line kisi bhi hidden space ya quotes ko saaf karegi
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
        
        if "Page Not Found" in response.text: return "🔴 BANNED (Broken)"
        return "⚠️ RATE LIMITED/LOGIN WALL"
    except Exception as e:
        return f"❌ PROXY/CONNECTION ERROR"

# --- COMMANDS ---
@bot.command()
async def status(ctx):
    p_status = "Connected ✅" if PROXY_RAW else "None ❌"
    await ctx.send(f"✅ **Monitor Online**\nInterval: `{INTERVAL_MINS}m`\nProxy: `{p_status}`")

@bot.command()
async def check(ctx, username: str):
    user = username.replace('@', '')
    await ctx.send(f"🔍 Checking @{user}...")
    res = check_instagram_status(user)
    await ctx.send(f"📊 **Result:** {res}")

# --- TASK ---
@tasks.loop(minutes=25)
async def monitor_loop():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    for user in ACCOUNTS:
        status = check_instagram_status(user)
        if "BANNED" in status:
            await channel.send(f"🚨 **ALERT:** @{user} is **BANNED**!")

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    keep_alive()
    if not monitor_loop.is_running():
        monitor_loop.change_interval(minutes=INTERVAL_MINS)
        monitor_loop.start()

if __name__ == "__main__":
    if TOKEN: bot.run(TOKEN)
