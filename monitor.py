import discord
from discord.ext import commands, tasks
import cloudscraper
import re
import os

# --- CONFIG ---
TOKEN = os.environ.get('DISCORD_TOKEN')
PROXY = os.environ.get('PROXY_URL') # Format: http://user:pass@ip:port
TARGET_CHANNEL = int(os.environ.get('CHANNEL_ID', 0))
ACCOUNTS = ["zuck", "instagram", "croprated"]

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
scraper = cloudscraper.create_scraper()

def check_ig_advanced(username):
    url = f"https://www.instagram.com/{username}/"
    proxies = {"http": PROXY, "https": PROXY} if PROXY else None
    
    try:
        # Request bhejna (Proxy ke saath)
        response = scraper.get(url, proxies=proxies, timeout=15)
        content = response.text

        # 1. Direct Ban Check (404)
        if response.status_code == 404:
            return "🔴 BANNED (404)"

        # 2. Advanced HTML Check (Followers/Posts/Bio)
        # Hum 'og:description' dhoondte hain jisme followers ka count hota hai
        meta_data = re.search(r'<meta content="(.*?)" name="description"', content)
        
        if meta_data:
            stats = meta_data.group(1) # Example: "10M Followers, 500 Posts..."
            if "Followers" in stats or "Posts" in stats:
                return f"🟢 ACTIVE ({stats})"
        
        # 3. Content Validation (Agar 200 OK hai par data nahi mila)
        if "Page Not Found" in content or "link you followed may be broken" in content:
            return "🔴 BANNED (Broken Link)"
            
        return "⚠️ RATE LIMITED (Login Wall Hit)"

    except Exception as e:
        return f"❌ ERROR ({str(e)})"

@bot.event
async def on_ready():
    print(f"✅ Monitor Bot Online: {bot.user}")
    auto_check.start()

@tasks.loop(minutes=30)
async def auto_check():
    channel = bot.get_channel(TARGET_CHANNEL)
    if not channel: return
    
    for user in ACCOUNTS:
        status = check_ig_advanced(user)
        if "BANNED" in status:
            await channel.send(f"🚨 **ALERT:** @{user} is **BANNED**!")

bot.run(TOKEN)
