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
# Ye Flask server Render ko "Live" signal dega aur port 8080 open rakhega.
app = Flask('')

@app.route('/')
def home():
    return "Monitor Bot is Running! Port 8080 is Active."

def run_flask():
    # Render default port 8080 use karta hai
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ==========================================
# ⚙️ CONFIGURATION (ENVIRONMENT VARIABLES)
# ==========================================
TOKEN = os.environ.get('DISCORD_TOKEN')
PROXY = os.environ.get('PROXY_URL') # Format: http://user:pass@ip:port
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))
# Default interval 25 mins taaki proxy block na ho
INTERVAL_MINS = int(os.environ.get('CHECK_INTERVAL', 25))

# Accounts List
ACCOUNTS = ["zuck", "croprated", "instagram"]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
scraper = cloudscraper.create_scraper()

# ==========================================
# 🔍 MONITORING LOGIC (ACCURATE)
# ==========================================
def check_instagram_status(username):
    url = f"https://www.instagram.com/{username}/"
    proxies = {"http": PROXY, "https": PROXY} if PROXY else None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = scraper.get(url, headers=headers, proxies=proxies, timeout=20)
        html = response.text

        # 1. 404 Check (Direct Ban)
        if response.status_code == 404:
            return "🔴 BANNED (404 Not Found)"

        # 2. Advanced Data Check (Followers, Posts)
        # Hum meta description se data extract kar rahe hain
        meta_data = re.search(r'<meta content="(.*?)" name="description"', html)
        
        if meta_data:
            stats = meta_data.group(1) # Example: "10M Followers, 500 Posts"
            if "Followers" in stats or "Posts" in stats:
                return f"🟢 ACTIVE ({stats})"
        
        # 3. Validation for Broken Links
        if "Page Not Found" in html or "link you followed may be broken" in html:
            return "🔴 BANNED (Broken Link)"

        # 4. Rate Limit / Login Wall Check
        if response.status_code == 429 or "login" in response.url:
            return "⚠️ RATE LIMITED (Proxy IP Flagged)"
            
        return "❓ DATA MISSING (Login Wall Hit)"

    except Exception as e:
        return f"❌ ERROR ({str(e)})"

# ==========================================
# 🤖 DISCORD BOT EVENTS & TASKS
# ==========================================
@bot.event
async def on_ready():
    print(f"✅ Monitor Bot Online as {bot.user}")
    print(f"✅ Check Interval: {INTERVAL_MINS} minutes")
    
    # Task ko start/restart karna safely
    if not monitor_loop.is_running():
        monitor_loop.change_interval(minutes=INTERVAL_MINS)
        monitor_loop.start()

@tasks.loop(minutes=25) # Placeholder, on_ready isey update kar dega
async def monitor_loop():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Error: CHANNEL_ID sahi nahi hai ya bot ko permission nahi hai.")
        return

    print("🔍 Starting Instagram check cycle...")
    for user in ACCOUNTS:
        status = check_instagram_status(user)
        
        # Agar status mein BANNED word hai, toh alert bhejega
        if "BANNED" in status:
            await channel.send(f"🚨 **ALERT:** Account @{user} is **BANNED**! \nDetails: `{status}`")
        else:
            print(f"Log: @{user} is {status}")

# ==========================================
# 🚀 EXECUTION START
# ==========================================
if __name__ == "__main__":
    # Pehle Flask (Port 8080) start hoga Render ke liye
    keep_alive() 
    
    # Phir Discord Bot start hoga
    if TOKEN:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"❌ Bot Crash: {e}")
    else:
        print("❌ ERROR: DISCORD_TOKEN missing in Environment Variables!")
