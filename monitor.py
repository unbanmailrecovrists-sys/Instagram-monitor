import os
import requests
import cloudscraper

# GitHub Secrets se data uthayega
TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# ACCOUNTS LIST: Yahan wo usernames dalo jo monitor karne hain
ACCOUNTS = ['zuck', 'croprated', 'okay.byie'] 
STATUS_FILE = "status.txt"

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})

def get_ig_status(username):
    try:
        url = f"https://www.instagram.com/{username}/"
        response = scraper.get(url, timeout=15)
        content = response.text.lower()
        ban_phrases = ["broken link", "content isn't available", "page isn't available"]
        
        if response.status_code == 404 or any(p in content for p in ban_phrases):
            return "BANNED"
        if response.status_code == 200:
            return "ACTIVE"
        return "ERROR"
    except:
        return "ERROR"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# Purana status load karna
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
    previous = old_status.get(user, "ACTIVE")

    if current == "BANNED" and previous == "ACTIVE":
        alerts += f"🚨 **ALERT: @{user} BAN ho gaya hai!**\n"
    elif current == "ACTIVE" and previous == "BANNED":
        alerts += f"✅ **GOOD NEWS: @{user} UNBAN (Recovered)!**\n"
    
    new_status_list.append(f"{user}:{current}")

with open(STATUS_FILE, "w") as f:
    f.write("\n".join(new_status_list))

if alerts:
    send_telegram(alerts)
