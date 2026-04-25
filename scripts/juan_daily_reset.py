import os, requests, json, sys, time
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN","")  # Juan
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID","")

with open("juan_daily_replenish.json") as f:
    cfg = json.load(f)
ITEMS = cfg.get("items", {})
QTY = cfg.get("qty_per_day", 15)

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

print(f"Daily reset Juan → {QTY}u por item")
print(f"Items: {list(ITEMS.values())}\n")

results = []
for cpid, iid in ITEMS.items():
    # Get current state
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    title = (g.get("title") or "")[:50]
    cur = g.get("available_quantity", 0)
    status = g.get("status","")
    
    if status != "active":
        print(f"  {iid} [{title}] status={status} → skip")
        results.append((iid, title, cur, None, "skip-"+status))
        continue
    
    # Set quantity back to QTY
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                     json={"available_quantity": QTY})
    new_qty = rp.json().get("available_quantity") if rp.status_code==200 else None
    print(f"  {iid} [{title}] {cur} → {new_qty} ({rp.status_code})")
    results.append((iid, title, cur, new_qty, rp.status_code))
    time.sleep(1)

# Telegram notify
if TG_TOKEN and TG_CHAT:
    lines = ["🔄 *Juan daily reset 15u*"]
    for iid, title, cur, new_qty, st in results:
        sold = max(0, QTY - cur) if isinstance(cur, int) else 0
        lines.append(f"• `{iid}` vendió {sold} ayer → reset a {new_qty}")
    msg = "\n".join(lines)
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id": TG_CHAT, "text": msg, "parse_mode": "Markdown"})
print("\nDone")
