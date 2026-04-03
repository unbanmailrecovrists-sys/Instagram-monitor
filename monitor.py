import discord
from discord.ext import commands, tasks
import cloudscraper
import re
import os

# Render Variables
TOKEN = os.environ.get('DISCORD_TOKEN')
PROXY = os.environ.get('PROXY_URL') 
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))

# Monitoring List
ACCOUNTS = ["zuck", "croprated", "urx.rupesh"]

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
scraper = cloudscraper.create_scraper()

def check_instagram(username):
    url = f"https://www.instagram.com/{username}/"
    # Proxy Setup
    proxies = {"http": PROXY, "https": PROXY}
    
    try:
        # Request with Proxy
        response = scraper.get(url, proxies=proxies, timeout=15)
        html = response.text

        # 1. Check for 404 (Direct Ban)
        if response.status_code == 404:
            return "🔴 BANNED (404)"

        # 2. Extract Followers/Posts from Meta Tags
        # Ye wahi logic hai jo pro bots use karte hain
        meta_content = re.search(r'<meta content="(.*?)" name="description"', html)
        
        if meta_content:
            data = meta_content.group(1) # Example: "10M Followers, 500 Posts"
            if "Followers" in data and "Posts" in data:
                return f"🟢 ACTIVE ({data})"

        # 3. Validation (Status 200 but no data)
        if "Page Not Found" in html or "Content Unavailable" in html:
            return "🔴 BANNED (Broken Link)"

        # 4. Login Wall/Rate Limit
        if response.status_code == 429 or "login" in response.url:
            return "⚠️ RATE LIMITED (Proxy Flagged)"

        return "❓ UNKNOWN STATUS"

    except Exception as e:
        return f"❌ PROXY/SERVER ERROR"

@bot.event
async def on_ready():
    print(f"✅ Pro Monitor Online with Proxy!")
    monitor_task.start()

@tasks.loop(minutes=20)
async def monitor_task():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    
    for user in ACCOUNTS:
        status = check_instagram(user)
        if "BANNED" in status:
            await channel.send(f"🚨 **ALERT:** @{user} is **BANNED**!")
        elif "RATE LIMITED" in status:
            print(f"Warning: Proxy IP for @{user} is getting flagged.")

bot.run(TOKEN)
