#!/usr/bin/env python3
"""
Multi-account catalog price war.
Sweeps all 6 accounts, finds catalog_listing items, drops $10 when losing buy box.
Floor protection: 70% of current price (or item-specific via floor_overrides).
Runs every 10 min via cron.
"""
import os, requests, json, time, sys

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN","")
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID","")

ACCOUNTS = [
    ("JUAN", "MELI_REFRESH_TOKEN"),
    ("CLARIBEL", "MELI_REFRESH_TOKEN_CLARIBEL"),
    ("ASVA", "MELI_REFRESH_TOKEN_ASVA"),
    ("RAYMUNDO", "MELI_REFRESH_TOKEN_RAYMUNDO"),
    ("DILCIE", "MELI_REFRESH_TOKEN_DILCIE"),
    ("MILDRED", "MELI_REFRESH_TOKEN_MILDRED"),
]

STEP = 10  # bajar $10 cada barrido cuando perdemos
DEFAULT_FLOOR_PCT = 0.55  # no bajar de 55% del current_price actual

# Floor overrides per item (optional, manually set)
FLOOR_OVERRIDES = {
    # "MLM2890793859": 350,  # ejemplo
}

# State file: tracks last_drop_at per item to avoid hammering same item too fast
STATE_FILE = "catalog_war_state.json"
try:
    state = json.load(open(STATE_FILE))
except:
    state = {"items": {}, "last_run": 0}

now = int(time.time())
report = []
total_changed = 0
total_won = 0
total_no_bbw = 0
total_floored = 0
total_skipped = 0

for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var, "")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
        USER_ID = me.get("id")
    except Exception as e:
        print(f"[{label}] auth err: {e}")
        continue

    print(f"\n=== {label} ({me.get('nickname')}) ===")
    
    # Find ALL active items (paginated)
    item_ids = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}", headers=H, timeout=15).json()
        b = rr.get("results", [])
        if not b: break
        item_ids.extend(b)
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    
    catalog_items = []
    for iid in item_ids:
        try:
            it = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,catalog_product_id,catalog_listing,status", headers=H, timeout=10).json()
        except:
            continue
        if it.get("catalog_listing") and it.get("catalog_product_id") and it.get("status") == "active":
            catalog_items.append(it)
    
    print(f"  Catalog listings activos: {len(catalog_items)}")
    
    for it in catalog_items:
        iid = it["id"]
        cpid = it["catalog_product_id"]
        title = (it.get("title") or "")[:35]
        our_price = float(it.get("price") or 0)
        if our_price <= 0: continue
        
        # Get buy box winner from catalog
        try:
            pr = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H, timeout=10).json()
        except:
            continue
        bbw = pr.get("buy_box_winner") or {}
        bbw_price = bbw.get("price")
        bbw_item = bbw.get("item_id")
        
        item_state = state["items"].get(iid, {})
        last_drop = item_state.get("last_drop_at", 0)
        
        if bbw_item == iid:
            total_won += 1
            print(f"    ✅ {iid} [{title}] ${int(our_price)} GANAMOS")
            continue
        if bbw_price is None:
            total_no_bbw += 1
            print(f"    ⊘ {iid} [{title}] ${int(our_price)} sin BBW")
            continue
        if our_price <= bbw_price:
            total_won += 1
            print(f"    ✅ {iid} [{title}] ${int(our_price)} (BBW ${bbw_price}) ya somos los mejores")
            continue
        
        # We're losing — drop $10
        original_price = item_state.get("original_price", our_price)
        # Update original if higher
        if our_price > original_price: original_price = our_price
        
        floor = FLOOR_OVERRIDES.get(iid, original_price * DEFAULT_FLOOR_PCT)
        candidate = our_price - STEP
        
        if candidate < floor:
            total_floored += 1
            print(f"    🛑 {iid} [{title}] ${int(our_price)} FLOOR ${int(floor)} (BBW ${bbw_price})")
            state["items"][iid] = {"original_price": original_price, "last_drop_at": last_drop, "floor": floor}
            continue
        
        # Smart: go to bbw_price - 1 if achievable (above floor)
        target = candidate
        if bbw_price - 1 >= floor and bbw_price - 1 < candidate:
            target = bbw_price - 1
        
        new_price = round(target, 0)
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"price": new_price}, timeout=15)
        if rp.status_code in (200,201):
            total_changed += 1
            msg = f"💸 {label} {iid} [{title}] ${int(our_price)}→${int(new_price)} (BBW ${bbw_price})"
            print(f"    {msg}")
            report.append(msg)
            state["items"][iid] = {
                "original_price": original_price,
                "last_drop_at": now,
                "floor": floor,
                "last_bbw": bbw_price,
                "label": title
            }
        else:
            print(f"    ❌ {iid} update err {rp.status_code}: {rp.text[:200]}")
        time.sleep(0.5)

state["last_run"] = now
json.dump(state, open(STATE_FILE,"w"), indent=2)

# Telegram report only if changes happened
if TG_TOKEN and TG_CHAT and report:
    msg_lines = [f"⚔️ *Catalog war: {total_changed} bajadas*"]
    msg_lines.extend(report[:20])
    if len(report) > 20:
        msg_lines.append(f"...+{len(report)-20} más")
    msg_lines.append(f"\n✅ Ganamos: {total_won} | 🛑 Floor: {total_floored} | ⊘ Sin BBW: {total_no_bbw}")
    body = "\n".join(msg_lines)
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id":TG_CHAT,"text":body[:4000],"parse_mode":"Markdown"})

print(f"\n=== RESUMEN ===")
print(f"Bajamos precio: {total_changed}")
print(f"Ya ganamos: {total_won}")
print(f"En floor: {total_floored}")
print(f"Sin BBW: {total_no_bbw}")
