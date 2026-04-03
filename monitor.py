import discord
from discord.ext import commands, tasks
import cloudscraper
import re
import os
import json
from flask import Flask
from threading import Thread
from datetime import datetime

# ==========================================
# 🌐 RENDER PORT FIX
# ==========================================
app = Flask('')
@app.route('/')
def home(): return "Pro Monitor is Online!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ==========================================
# ⚙️ CONFIG & DATA (JSON DB for Simplicity)
# ==========================================
TOKEN = os.environ.get('DISCORD_TOKEN')
PROXY_URL = os.environ.get('PROXY_URL')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))
DB_FILE = "monitor_data.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
scraper = cloudscraper.create_scraper()

# ==========================================
# 🎨 PRO EMBED CREATOR
# ==========================================
def create_log_embed(user, status, color, details=""):
    embed = discord.Embed(
        title="✨ Instagram Status Update",
        description=f"Account: **@{user}**",
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="Current Status", value=f"`{status}`", inline=True)
    if details:
        embed.add_field(name="Details", value=f"*{details}*", inline=False)
    embed.set_footer(text="Verox Pro Monitor", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    return embed

# ==========================================
# 🔍 SCAN LOGIC
# ==========================================
def check_status(username):
    url = f"https://www.instagram.com/{username}/"
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"}
    
    try:
        response = scraper.get(url, headers=headers, proxies=proxies, timeout=15)
        if response.status_code == 404: return "BANNED", "404 Not Found"
        
        html = response.text
        meta = re.search(r'<meta content="(.*?)" name="description"', html)
        if meta:
            stats = meta.group(1)
            if "Followers" in stats or "Posts" in stats:
                return "ACTIVE", stats
        
        if "Page Not Found" in html: return "BANNED", "Broken Link"
        return "ERROR", "Rate Limited / Login Wall"
    except Exception as e:
        return "ERROR", str(e)

# ==========================================
# 🤖 PRO COMMANDS
# ==========================================

@bot.command()
async def add(ctx, username: str):
    user = username.replace('@', '').lower()
    db = load_db()
    status, details = check_status(user)
    db[user] = status
    save_db(db)
    embed = create_log_embed(user, status, discord.Color.blue(), f"Added to database. {details}")
    await ctx.send(embed=embed)

@bot.command()
async def remove(ctx, username: str):
    user = username.replace('@', '').lower()
    db = load_db()
    if user in db:
        del db[user]
        save_db(db)
        await ctx.send(f"🗑️ **@{user}** removed from monitor.")
    else:
        await ctx.send("❌ User not found.")

@bot.command()
async def list(ctx):
    db = load_db()
    if not db: return await ctx.send("📋 List is empty.")
    names = "\n".join([f"• @{u} [`{s}`]" for u, s in db.items()])
    await ctx.send(f"📋 **Monitored Accounts:**\n{names}")

# ==========================================
# 🔄 MONITOR LOOP (AUTO)
# ==========================================
@tasks.loop(minutes=25)
async def monitor_task():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    
    db = load_db()
    for user, last_status in list(db.items()):
        current_status, details = check_status(user)
        
        # UNBAN ALERT
        if last_status == "BANNED" and current_status == "ACTIVE":
            embed = create_log_embed(user, "🟢 UNBANNED", discord.Color.green(), f"Account is back! {details}")
            await channel.send(embed=embed)
            db[user] = "ACTIVE"
        
        # NEW BAN ALERT
        elif last_status == "ACTIVE" and current_status == "BANNED":
            embed = create_log_embed(user, "🔴 BANNED", discord.Color.red(), f"Account just got hit! {details}")
            await channel.send(embed=embed)
            db[user] = "BANNED"
            
        save_db(db)

@bot.event
async def on_ready():
    print(f"🚀 Verox Pro Monitor Online: {bot.user}")
    keep_alive()
    if not monitor_task.is_running():
        monitor_task.start()

if __name__ == "__main__":
    bot.run(TOKEN)