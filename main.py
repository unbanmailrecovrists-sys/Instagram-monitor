import discord
from discord.ext import tasks, commands
import requests
import time
from flask import Flask
from threading import Thread

# --- WEB SERVER FOR 24/7 ---
# Ye part Render/UptimeRobot ke liye zaroori hai
app = Flask('')

@app.route('/')
def home():
    return "Bot is live and monitoring!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT CONFIGURATION ---
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = 1481540811299622943

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Monitoring list (Username: Start_Time)
monitored_accounts = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    if not monitor_loop.is_running():
        monitor_loop.start()

# --- COMMANDS ---

@bot.command()
async def add(ctx, username: str):
    """Account ko monitor list mein add karein: !add username"""
    # Username se '@' hatana agar user ne likha ho
    clean_username = username.replace('@', '')
    monitored_accounts[clean_username] = time.time()
    
    embed = discord.Embed(title="Monitoring Status", color=0xff0000)
    embed.description = f"User @{clean_username} is being monitored!"
    await ctx.send(embed=embed)

@bot.command()
async def list(ctx):
    """Monitored accounts ki list dekhne ke liye: !list"""
    if not monitored_accounts:
        await ctx.send("List khali hai! Use `!add username` to monitor.")
        return
    
    desc = "\n".join([f"• @{u}" for u in monitored_accounts.keys()])
    embed = discord.Embed(title="✅ Unban Monitor List", description=desc, color=0x00ff00)
    await ctx.send(embed=embed)

# --- MONITORING LOOP ---

@tasks.loop(minutes=5)
async def monitor_loop():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    for username, start_time in list(monitored_accounts.items()):
        url = f"https://www.instagram.com/{username}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        
        try:
            # Instagram check karna
            response = requests.get(url, headers=headers, timeout=10)
            
            # Agar status code 200 hai, matlab account recover ho gaya
            if response.status_code == 200:
                end_time = time.time()
                total_seconds = int(end_time - start_time)
                
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60

                embed = discord.Embed(title="Monitoring Status", color=0x00ff00)
                embed.description = f"**Account Recovered | @{username}** 🏆 ✅"
                embed.add_field(
                    name="⏱️ Time taken", 
                    value=f"{hours} hours, {minutes} minutes, {seconds} seconds",
                    inline=False
                )
                
                await channel.send(embed=embed)
                
                # Account ko list se remove karein
                del monitored_accounts[username]
                
        except Exception as e:
            print(f"Error checking {username}: {e}")

# --- START BOT ---
if __name__ == "__main__":
    keep_alive() # Web server start
    bot.run(TOKEN)
