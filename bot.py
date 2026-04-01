import os
import asyncio
import logging
from datetime import datetime

import requests
from instagrapi import Client
from instagrapi.exceptions import (
    UserNotFound,
    ClientError,
    ClientLoginRequired,
    ClientConnectionError,
)

import discord
from discord.ext import commands, tasks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# ─── CONFIG ───────────────────────────────────────────────
DISCORD_TOKEN      = os.environ.get("DISCORD_TOKEN", "")
DISCORD_WEBHOOK    = os.environ.get("DISCORD_WEBHOOK", "")
ALERT_CHANNEL_ID   = int(os.environ.get("ALERT_CHANNEL_ID", "0"))
CHECK_INTERVAL_MIN = int(os.environ.get("CHECK_INTERVAL_MINUTES", "10"))
IG_USERNAME        = os.environ.get("IG_USERNAME", "")
IG_PASSWORD        = os.environ.get("IG_PASSWORD", "")

USERNAMES_RAW = os.environ.get("INSTAGRAM_USERNAMES", "")
monitored    = set(u.strip().lower().lstrip("@") for u in USERNAMES_RAW.split(",") if u.strip())
banned_state = set()

# ─── INSTAGRAM CLIENT ─────────────────────────────────────
cl = Client()
ig_logged_in = False

def ig_login():
    global ig_logged_in
    try:
        cl.login(IG_USERNAME, IG_PASSWORD)
        ig_logged_in = True
        log.info(f"Instagram login successful: @{IG_USERNAME}")
    except Exception as e:
        ig_logged_in = False
        log.error(f"Instagram login failed: {e}")

def check_instagram(username: str) -> str:
    """active | banned | error"""
    global ig_logged_in
    if not ig_logged_in:
        ig_login()
        if not ig_logged_in:
            return "error"
    try:
        user = cl.user_info_by_username(username)
        if user:
            return "active"
        return "banned"
    except UserNotFound:
        return "banned"
    except ClientLoginRequired:
        log.warning("Session expired — re-logging in")
        ig_login()
        return "error"
    except ClientConnectionError as e:
        log.warning(f"Connection error: {e}")
        return "error"
    except ClientError as e:
        msg = str(e).lower()
        if "not found" in msg or "no user" in msg:
            return "banned"
        log.warning(f"@{username} client error: {e}")
        return "error"
    except Exception as e:
        log.warning(f"@{username} unknown error: {e}")
        return "error"

# ─── BOT SETUP ────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─── DISCORD ALERTS ───────────────────────────────────────
def send_webhook_alert(username: str, status: str):
    if not DISCORD_WEBHOOK:
        return
    if status == "banned":
        color, title = 0xE74C3C, f"🚫 Account Banned: @{username}"
        desc = (
            f"Instagram account **@{username}** ban ho gaya hai!\n\n"
            f"[Profile check karo](https://www.instagram.com/{username}/)\n\n"
            f"**Time:** {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
        )
    else:
        color, title = 0x2ECC71, f"✅ Account Wapas Active: @{username}"
        desc = (
            f"Instagram account **@{username}** wapas active ho gaya!\n\n"
            f"[Profile dekho](https://www.instagram.com/{username}/)\n\n"
            f"**Time:** {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
        )
    payload = {"embeds": [{
        "title": title, "description": desc, "color": color,
        "footer": {"text": "Instagram Ban Monitor • 24/7"},
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }]}
    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
    except Exception as e:
        log.error(f"Webhook fail: {e}")

async def send_channel_alert(username: str, banned: bool):
    if not ALERT_CHANNEL_ID:
        return
    ch = bot.get_channel(ALERT_CHANNEL_ID)
    if not ch:
        return
    embed = discord.Embed(
        title=f"{'🚫 BANNED' if banned else '✅ WAPAS ACTIVE'}: @{username}",
        description=f"[Instagram pe dekho](https://www.instagram.com/{username}/)",
        color=0xE74C3C if banned else 0x2ECC71,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Instagram Ban Monitor")
    await ch.send(embed=embed)

# ─── AUTO MONITOR LOOP ────────────────────────────────────
@tasks.loop(minutes=CHECK_INTERVAL_MIN)
async def monitor_loop():
    if not monitored:
        return
    log.info(f"Auto-check: {len(monitored)} accounts")
    for username in list(monitored):
        result = await asyncio.to_thread(check_instagram, username)
        log.info(f"@{username} → {result.upper()}")
        if result == "banned" and username not in banned_state:
            banned_state.add(username)
            send_webhook_alert(username, "banned")
            await send_channel_alert(username, banned=True)
        elif result == "active" and username in banned_state:
            banned_state.discard(username)
            send_webhook_alert(username, "restored")
            await send_channel_alert(username, banned=False)
        await asyncio.sleep(3)

@monitor_loop.before_loop
async def before_monitor():
    await bot.wait_until_ready()

# ─── EVENTS ───────────────────────────────────────────────
@bot.event
async def on_ready():
    log.info(f"✅ Bot ready: {bot.user}")
    log.info(f"   Monitoring: {monitored or 'koi nahi (use !add)'}")
    await asyncio.to_thread(ig_login)
    monitor_loop.start()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❓ Command nahi pehchana. `!help` dekho.")
    else:
        log.error(f"Command error: {error}")

# ─── COMMANDS ─────────────────────────────────────────────
@bot.command(name="add")
async def cmd_add(ctx, *, username: str = None):
    if not username:
        await ctx.send("❌ **Usage:** `!add username`")
        return
    username = username.strip().lower().lstrip("@")
    if username in monitored:
        await ctx.send(f"⚠️ **@{username}** pehle se monitor ho raha hai!")
        return
    monitored.add(username)
    embed = discord.Embed(
        title="✅ Username Add Ho Gaya",
        description=(
            f"**@{username}** monitor list mein add!\n"
            f"Har **{CHECK_INTERVAL_MIN} min** mein auto-check hoga.\n\n"
            f"Abhi check karne ke liye `!check {username}` karo."
        ),
        color=0x2ECC71
    )
    embed.set_footer(text=f"Total monitored: {len(monitored)}")
    await ctx.send(embed=embed)

@bot.command(name="remove")
async def cmd_remove(ctx, *, username: str = None):
    if not username:
        await ctx.send("❌ **Usage:** `!remove username`")
        return
    username = username.strip().lower().lstrip("@")
    if username not in monitored:
        await ctx.send(f"⚠️ **@{username}** list mein nahi hai!")
        return
    monitored.discard(username)
    banned_state.discard(username)
    embed = discord.Embed(
        title="🗑️ Username Hata Diya",
        description=f"**@{username}** monitor list se remove ho gaya.",
        color=0xE67E22
    )
    embed.set_footer(text=f"Total monitored: {len(monitored)}")
    await ctx.send(embed=embed)

@bot.command(name="status")
async def cmd_status(ctx):
    if not monitored:
        await ctx.send("📋 Monitor list khaali hai. `!add username` se shuru karo.")
        return
    embed = discord.Embed(title="📋 Monitor Status", color=0x5865F2, timestamp=datetime.utcnow())
    lines = []
    for u in sorted(monitored):
        lines.append(f"{'🚫' if u in banned_state else '✅'} **@{u}** — {'Banned' if u in banned_state else 'Active'}")
    embed.description = "\n".join(lines)
    embed.set_footer(text=f"Total: {len(monitored)} | Auto-check: har {CHECK_INTERVAL_MIN} min")
    await ctx.send(embed=embed)

@bot.command(name="check")
async def cmd_check(ctx, *, username: str = None):
    if username:
        username = username.strip().lower().lstrip("@")
        msg = await ctx.send(f"🔍 **@{username}** check ho raha hai...")
        result = await asyncio.to_thread(check_instagram, username)
        colors = {"active": 0x2ECC71, "banned": 0xE74C3C, "error": 0x95A5A6}
        titles = {
            "active": f"✅ @{username} — Active",
            "banned": f"🚫 @{username} — Banned!",
            "error":  f"⚠️ @{username} — Check Error"
        }
        embed = discord.Embed(title=titles[result], color=colors[result])
        embed.set_footer(text=f"Checked at {datetime.now().strftime('%I:%M %p')}")
        await msg.edit(content=None, embed=embed)
        if result == "banned" and username not in banned_state:
            banned_state.add(username)
            send_webhook_alert(username, "banned")
        elif result == "active" and username in banned_state:
            banned_state.discard(username)
            send_webhook_alert(username, "restored")
        return

    if not monitored:
        await ctx.send("📋 Monitor list khaali hai.")
        return
    msg = await ctx.send(f"🔍 **{len(monitored)}** accounts check ho rahe hain...")
    results = {}
    for u in sorted(monitored):
        results[u] = await asyncio.to_thread(check_instagram, u)
        if results[u] == "banned" and u not in banned_state:
            banned_state.add(u)
            send_webhook_alert(u, "banned")
            await send_channel_alert(u, banned=True)
        elif results[u] == "active" and u in banned_state:
            banned_state.discard(u)
            send_webhook_alert(u, "restored")
            await send_channel_alert(u, banned=False)
        await asyncio.sleep(3)

    icons  = {"active": "✅", "banned": "🚫", "error": "⚠️"}
    labels = {"active": "Active", "banned": "Banned!", "error": "Error"}
    lines  = [f"{icons[r]} **@{u}** — {labels[r]}" for u, r in sorted(results.items())]
    embed  = discord.Embed(
        title="🔍 Manual Check Complete",
        description="\n".join(lines),
        color=0x5865F2,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Naye changes par alerts bhej diye")
    await msg.edit(content=None, embed=embed)

@bot.command(name="help")
async def cmd_help(ctx):
    embed = discord.Embed(title="📖 Instagram Ban Monitor — Commands", description="Prefix: `!`", color=0x5865F2)
    embed.add_field(name="`!add <username>`",    value="Naya account monitor karo",     inline=False)
    embed.add_field(name="`!remove <username>`", value="Account monitor se hatao",       inline=False)
    embed.add_field(name="`!status`",            value="Sab accounts ka status dekho",   inline=False)
    embed.add_field(name="`!check`",             value="Turant sab check karo",          inline=False)
    embed.add_field(name="`!check <username>`",  value="Ek specific account check karo", inline=False)
    embed.set_footer(text=f"Auto-check har {CHECK_INTERVAL_MIN} min mein hota hai")
    await ctx.send(embed=embed)

# ─── RUN ──────────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        log.error("DISCORD_TOKEN set nahi!")
    elif not IG_USERNAME or not IG_PASSWORD:
        log.error("IG_USERNAME ya IG_PASSWORD set nahi!")
    else:
        bot.run(DISCORD_TOKEN)
