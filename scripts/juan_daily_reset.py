import os, requests, json, sys, time
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN","")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID","")

# Catalog items (Juan)
with open("juan_daily_replenish.json") as f:
    cfg = json.load(f)
ITEMS = cfg.get("items", {})  # cpid → iid
DAILY_QTY = cfg.get("qty_per_day", 15)
VISIBLE = 1  # only show 1 piece on MELI

# Load stock_config to update real_stock
with open("stock_config.json") as f:
    stock = json.load(f)

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

print(f"Daily reset Juan (catálogo $499): real_stock={DAILY_QTY}, visible={VISIBLE}\n")

results = []
for cpid, iid in ITEMS.items():
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    title = (g.get("title") or "")[:45]
    cur_visible = g.get("available_quantity", 0)
    status = g.get("status","")
    
    # Calculate sales since last reset
    prev_real = stock.get(iid, {}).get("real_stock", DAILY_QTY)
    sold = max(0, prev_real - cur_visible) if status == "active" else 0
    
    # Reset real_stock in bot config
    if iid in stock:
        stock[iid]["real_stock"] = DAILY_QTY
    
    if status != "active":
        print(f"  {iid} [{title}] status={status} → real_stock=15 (no visible touch)")
        results.append((iid, title, cur_visible, sold, "skip-"+status))
        continue
    
    # Set MELI visible to 1
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                     json={"available_quantity": VISIBLE})
    new_visible = rp.json().get("available_quantity") if rp.status_code==200 else None
    print(f"  {iid} [{title}] vendió_ayer={sold} | visible {cur_visible}→{new_visible} | real_stock→{DAILY_QTY}")
    results.append((iid, title, cur_visible, sold, rp.status_code))
    time.sleep(1)

# Save updated stock_config
with open("stock_config.json","w") as f:
    json.dump(stock, f, indent=2, ensure_ascii=False)

# Telegram notify
if TG_TOKEN and TG_CHAT:
    total_sold = sum(s for (_,_,_,s,_) in results if isinstance(s,int))
    revenue = total_sold * 499
    lines = [f"🔄 *Juan reset 24h* (catálogo $499)", f"Vendido ayer: *{total_sold}u = ${revenue:,}*"]
    for iid, title, _, sold, st in results:
        lines.append(f"• `{iid}`: {sold}u (visible→1, stock→15)")
    msg = "\n".join(lines)
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id": TG_CHAT, "text": msg, "parse_mode": "Markdown"})
print("\nDone")
