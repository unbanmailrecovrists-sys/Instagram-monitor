import discord
from discord.ext import commands, tasks
import instaloader
import os
import time

# --- CONFIG ---
TOKEN = os.environ.get('DISCORD_TOKEN') # Discord Bot Token
IG_USER = "monitor_ig"        # Instagram Username
IG_PASS = "1q2w3e4r5t"        # Instagram Password
CHANNEL_ID = int(os.environ.get('CHANNEL_ID', 0))
ACCOUNTS = ['zuck', 'croprated', 'urx.rupesh']

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Instaloader Setup
L = instaloader.Instaloader()

def login_instagram():
    try:
        # Session file check karega taaki baar-baar login na karna pade
        session_file = f"session_{IG_USER}"
        if os.path.exists(session_file):
            L.load_session_from_file(IG_USER, filename=session_file)
            print("✅ Session loaded from file!")
        else:
            L.login(IG_USER, IG_PASS)
            L.save_session_to_file(filename=session_file)
            print("✅ New Login Successful!")
    except Exception as e:
        print(f"❌ Login Failed: {e}")

def get_status(username):
    try:
        # Real login session ke sath check
        instaloader.Profile.from_username(L.context, username)
        return "ACTIVE"
    except instaloader.exceptions.ProfileNotExistsException:
        return "BANNED"
    except instaloader.exceptions.ConnectionException:
        return "RATE_LIMIT (IP Blocked)"
    except Exception:
        return "ERROR"

@bot.event
async def on_ready():
    print(f"✅ Bot Online: {bot.user}")
    login_instagram()
    auto_monitor.start()

@bot.command()
async def check(ctx, user: str):
    user = user.replace('@', '').lower()
    await ctx.send(f"🔍 Checking **@{user}** using Login Session...")
    status = get_status(user)
    await ctx.send(f"📊 **@{user}** status: **{status}**")

@tasks.loop(minutes=20)
async def auto_monitor():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return
    for user in ACCOUNTS:
        status = get_status(user)
        if status == "BANNED":
            await channel.send(f"🚨 **ALERT:** @{user} is **BANNED**!")
        time.sleep(10) # Gap taaki IG ko shak na ho

bot.run(TOKEN)