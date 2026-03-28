import os
import requests
import cloudscraper

# CONFIG (Yahan apna Webhook URL dalo)
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1487352962400391208/Uh2P1nrMIXxHJIwI2xnOQOCpaN1qi-LnQCcHRsHknSglabIT3N-YB2ZLfembg7PY4UGH"
ACCOUNTS = ['zuck', 'croprated', 'urx.ganesh'] 
STATUS_FILE = "status.txt"

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})

def get_ig_status(username):
    url = f"https://www.instagram.com/{username}/"
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code == 404:
            return "BANNED"
        if response.status_code == 200:
            return "ACTIVE"
        return "ERROR"
    except:
        return "ERROR"

def send_discord(msg):
    requests.post(DISCORD_WEBHOOK, json={"content": msg})

# Load old status
old_status = {}
if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, "r") as f:
        for line in f:
            if ":" in line:
                u, s = line.strip().split(":")
                old_status[u] = s

new_status_list = []
alerts = ""

for user in ACCOUNTS:
    current = get_ig_status(user)
    if current == "ERROR": continue
    
    previous = old_status.get(user, "ACTIVE")
    if current == "BANNED" and previous == "ACTIVE":
        alerts += f"🚨 **BAN ALERT:** @{user} is now **BANNED**!\n"
    elif current == "ACTIVE" and previous == "BANNED":
        alerts += f"✅ **UNBAN ALERT:** @{user} is **RECOVERED**!\n"
    
    new_status_list.append(f"{user}:{current}")

with open(STATUS_FILE, "w") as f:
    f.write("\n".join(new_status_list))

if alerts:
    send_discord(alerts)
else:
    # Optional: Bas ye dekhne ke liye ki bot zinda hai
    print("Everything is same. No alerts.")
