import os, requests, json, time
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN_CLARIBEL","")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID","")

with open("stock_config_claribel.json") as f:
    cfg = json.load(f)

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

print("Claribel daily reset (24h)\n")
results = []
for iid, info in cfg.items():
    if not info.get("active"): continue
    
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    title = (g.get("title","") or "")[:45]
    status = g.get("status","")
    
    if info.get("type") == "catalog_no_variations":
        # Single SKU catalog item: reset real_stock=daily_reset_to, visible=1
        target = info.get("daily_reset_to", 10)
        info["real_stock"] = target
        cur = g.get("available_quantity",0)
        if status != "active":
            print(f"  {iid} [{title}] status={status} → real→{target} (no MELI touch)")
            continue
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                         json={"available_quantity": 1})
        sold = max(0, target - cur) if cur >= 0 else 0
        print(f"  {iid} [{title}] vendió_24h={sold} | visible {cur}→1 | real→{target}")
        results.append((iid, title, sold, info["price"]))
    elif info.get("variations"):
        # Variations item: reset each color's real to its original
        target_per_color = info.get("daily_reset_to", 10)
        for color in info["variations"]:
            info["variations"][color] = target_per_color
        # Don't touch MELI variations directly here - claribel_replenish handles per-variation
        print(f"  {iid} [{title}] variations real_stock→{target_per_color} cada color")
    time.sleep(0.5)

with open("stock_config_claribel.json","w") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)

if TG_TOKEN and TG_CHAT and results:
    total_sold = sum(s for _,_,s,_ in results)
    revenue = sum(s*p for _,_,s,p in results)
    lines = [f"🔄 *Claribel reset 24h*", f"Vendido: *{total_sold}u = ${int(revenue):,}*"]
    for iid,t,s,p in results:
        lines.append(f"• `{iid}` ({t[:25]}): {s}u")
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id":TG_CHAT,"text":"\n".join(lines),"parse_mode":"Markdown"})
print("\nDone")
