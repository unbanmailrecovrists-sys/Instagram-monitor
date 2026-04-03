import discord
from discord.ext import commands, tasks
import cloudscraper
import re
import os

# --- RENDER ENVIRONMENT VARIABLES ---
TOKEN = os.environ.get('DISCORD_TOKEN')
PROXY = os.environ.get('PROXY_URL') 
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))
# Default 20 minutes rakha hai agar Render mein variable na ho
INTERVAL_MINS = int(os.environ.get('CHECK_INTERVAL', 20)) 

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
scraper = cloudscraper.create_scraper()

def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    proxies = {"http": PROXY, "https": PROXY}
    
    try:
        response = scraper.get(url, proxies=proxies, timeout=15)
        html = response.text

        if response.status_code == 404:
            return "🔴 BANNED (404)"

        meta_content = re.search(r'<meta content="(.*?)" name="description"', html)
        if meta_content:
            data = meta_content.group(1)
            if "Followers" in data and "Posts" in data:
                return f"🟢 ACTIVE ({data})"

        if "Page Not Found" in html or "Content Unavailable" in html:
            return "🔴 BANNED (Broken Link)"

        return "⚠️ RATE LIMITED/LOGIN WALL"
    except Exception:
        return "❌ PROXY ERROR"

@bot.event
async def on_ready():
    print(f"✅ Monitor Bot Online | Interval: {INTERVAL_MINS}m")
    # Task start hone se pehle purani stop karega taaki duplicate na chale
    if monitor_task.is_running():
        monitor_task.stop()
    monitor_task.change_interval(minutes=INTERVAL_MINS)
    monitor_task.start()

@tasks.loop(minutes=20) # Ye default hai, on_ready isey change kar dega
async def monitor_task():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    
    # Aapka list file ya static list
    ACCOUNTS = ["zuck", "croprated"] 
    
    for user in ACCOUNTS:
        status = check_instagram(user)
        if "BANNED" in status:
            await channel.send(f"🚨 **ALERT:** @{user} is **BANNED**!")

bot.run(TOKEN)
