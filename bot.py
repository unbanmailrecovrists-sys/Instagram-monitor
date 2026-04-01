import os
import time
import asyncio
import logging
import requests
from datetime import datetime
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

USERNAMES_RAW = os.environ.get("INSTAGRAM_USERNAMES", "")
monitored     = set(u.strip().lower().lstrip("@") for u in USERNAMES_RAW.split(",") if u.strip())
banned_state  = set()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ─── BOT SETUP ────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ─── INSTAGRAM CHECK ──────────────────────────────────────
def check_instagram(username: str) -> str:
    url = f"https://www.instagram.com/{username}/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if r.status_code == 404:
            return "banned"
        if r.status_code == 200:
            if '"user":null' in r.text or "Sorry, this page" in r.text:
                return "banned"
            return "active"
        return "error"
    except Exception as e:
        log.warning(f"@{username} check error: {e}")
        return "error"

# ─── DISCORD ALERT ────────────────────────────────────────
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
        await asyncio.sleep(2)

@monitor_loop.before_loop
async def before_monitor():
    await bot.wait_until_ready()

# ─── EVENTS ───────────────────────────────────────────────
@bot.event
async def on_ready():
    log.info(f"✅ Bot ready: {bot.user}")
    log.info(f"   Monitoring: {monitored or 'koi nahi (use !add)'}")
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
    """!add username — account add karo monitor mein"""
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
    log.info(f"Added @{username} by {ctx.author}")


@bot.command(name="remove")
async def cmd_remove(ctx, *, username: str = None):
    """!remove username — account hatao"""
    if not username:
        await ctx.send("❌ **Usage:** `!remove username`")
        return
    username = username.strip().lower().lstrip("@")
    if username not in monitored:
        await ctx.send(f"⚠️ **@{username}** list mein nahi hai! `!status` se list dekho.")
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
    log.info(f"Removed @{username} by {ctx.author}")


@bot.command(name="status")
async def cmd_status(ctx):
    """!status — sab accounts ka status dekho"""
    if not monitored:
        await ctx.send("📋 Monitor list khaali hai. `!add username` se shuru karo.")
        return
    embed = discord.Embed(
        title="📋 Monitor Status",
        color=0x5865F2,
        timestamp=datetime.utcnow()
    )
    lines = []
    for u in sorted(monitored):
        if u in banned_state:
            lines.append(f"🚫 **@{u}** — Banned")
        else:
            lines.append(f"✅ **@{u}** — Active")
    embed.description = "\n".join(lines)
    embed.set_footer(text=f"Total: {len(monitored)} | Auto-check: har {CHECK_INTERVAL_MIN} min")
    await ctx.send(embed=embed)


@bot.command(name="check")
async def cmd_check(ctx, *, username: str = None):
    """!check [username] — turant check karo"""
    # Specific username
    if username:
        username = username.strip().lower().lstrip("@")
        msg = await ctx.send(f"🔍 **@{username}** check ho raha hai...")
        result = await asyncio.to_thread(check_instagram, username)
        colors  = {"active": 0x2ECC71, "banned": 0xE74C3C, "error": 0x95A5A6}
        titles  = {"active": f"✅ @{username} — Active", "banned": f"🚫 @{username} — Banned!", "error": f"⚠️ @{username} — Check Error"}
        embed = discord.Embed(title=titles[result], color=colors[result])
        embed.set_footer(text=f"Checked at {datetime.now().strftime('%I:%M %p')}")
        await msg.edit(content=None, embed=embed)
        # State update
        if result == "banned" and username not in banned_state:
            banned_state.add(username)
            send_webhook_alert(username, "banned")
        elif result == "active" and username in banned_state:
            banned_state.discard(username)
            send_webhook_alert(username, "restored")
        return

    # Sab check karo
    if not monitored:
        await ctx.send("📋 Monitor list khaali hai. `!add username` se shuru karo.")
        return
    msg = await ctx.send(f"🔍 **{len(monitored)}** accounts check ho rahe hain... thoda wait karo.")
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
        await asyncio.sleep(2)

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
    """!help — commands ki list"""
    embed = discord.Embed(
        title="📖 Instagram Ban Monitor — Commands",
        description="Prefix: `!`",
        color=0x5865F2
    )
    embed.add_field(name="`!add <username>`",    value="Naya account monitor karo",           inline=False)
    embed.add_field(name="`!remove <username>`", value="Account monitor se hatao",             inline=False)
    embed.add_field(name="`!status`",            value="Sab accounts ka status dekho",         inline=False)
    embed.add_field(name="`!check`",             value="Abhi turant sab accounts check karo",  inline=False)
    embed.add_field(name="`!check <username>`",  value="Sirf ek specific account check karo",  inline=False)
    embed.set_footer(text=f"Auto-check har {CHECK_INTERVAL_MIN} min mein hota hai")
    await ctx.send(embed=embed)


# ─── RUN ──────────────────────────────────────────────────
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        log.error("DISCORD_TOKEN environment variable set nahi! Bot band ho raha hai.")
    else:
        bot.run(DISCORD_TOKEN)
