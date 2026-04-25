#!/usr/bin/env python3
"""
Multi-account catalog price war v4 — STAIRCASE STRATEGY
- Designated winner_account (CLARIBEL) gets target price = ext_competitor - $10
- Other accounts get target = winner_target + STAIRCASE_GAP (escalonado)
- Excludes OUR OWN items from "cheapest competitor" search (no auto-canibalismo)
- Floor 55%, Ceiling 130% por item
"""
import os, requests, json, time

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

WINNER_ACCOUNT = "CLARIBEL"
GAP = 10                         # winner = ext_competitor - $10
STAIRCASE_GAP = 50               # cada cuenta sucesiva: winner + N*50
STAIRCASE_ORDER = ["JUAN", "ASVA", "RAYMUNDO", "DILCIE", "MILDRED"]  # orden ascendente del escalón
DEFAULT_FLOOR_PCT = 0.55
MIN_FLOOR_PRICE = 299  # piso absoluto: nunca bajar de $299
DEFAULT_CEIL_PCT  = 1.30
MIN_DELTA = 5                    # solo cambiar si delta ≥ $5

FLOOR_OVERRIDES = {}
CEIL_OVERRIDES = {}

STATE_FILE = "catalog_war_state.json"
try: state = json.load(open(STATE_FILE))
except: state = {"items": {}, "last_run": 0}

now = int(time.time())
report_down = []
report_up = []
report_stair = []
total_down = total_up = total_stair = total_won = total_no_data = total_floored = 0

# ====== PHASE 1: collect tokens + all our catalog items ======
tokens = {}
our_items = []  # list of dicts: {account, iid, cpid, price, title, H, original_price}
print("=== PHASE 1: Recolectar publicaciones de catálogo ===\n")

for label, env_var in ACCOUNTS:
    RT = os.environ.get(env_var, "")
    if not RT: continue
    try:
        r = requests.post("https://api.mercadolibre.com/oauth/token", data={
            "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
        }).json()
        tokens[label] = r["access_token"]
        H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
        me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
        USER_ID = me.get("id")
    except Exception as e:
        print(f"[{label}] auth err: {e}"); continue
    
    item_ids = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}", headers=H, timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        item_ids.extend(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    
    cnt = 0
    for iid in item_ids:
        try:
            it = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,catalog_product_id,catalog_listing,status", headers=H, timeout=10).json()
        except: continue
        if it.get("catalog_listing") and it.get("catalog_product_id") and it.get("status")=="active":
            our_items.append({
                "account": label, "iid": iid, "cpid": it["catalog_product_id"],
                "price": float(it.get("price") or 0),
                "title": (it.get("title") or "")[:35],
                "H": H
            })
            cnt += 1
    print(f"  {label}: {cnt} catalog listings")

print(f"\nTotal catalog listings nuestros: {len(our_items)}")

# ====== PHASE 2: agrupar por catalog_product_id ======
by_cpid = {}
all_our_iids = set()
for it in our_items:
    by_cpid.setdefault(it["cpid"], []).append(it)
    all_our_iids.add(it["iid"])

print(f"\nCPIDs únicos: {len(by_cpid)} | items totales: {len(our_items)}\n")

# ====== PHASE 3: por cada CPID, calcular target prices ======
print("=== PHASE 3: Strategy escalonada ===\n")

for cpid, items in by_cpid.items():
    # External competitor (excluding all our IDs)
    use_H = items[0]["H"]
    has_full = False
    try:
        r = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=30", headers=use_H, timeout=10).json()
        ext_competitors = [c for c in r.get("results",[]) if c.get("item_id") not in all_our_iids]
        # Detect FULL competitors
        for c in ext_competitors:
            if (c.get("shipping",{}) or {}).get("logistic_type") == "fulfillment":
                has_full = True
                break
        if ext_competitors:
            ext_cheapest = min(ext_competitors, key=lambda x: float(x.get("price") or 999999))
            ext_price = float(ext_cheapest.get("price"))
            ext_iid = ext_cheapest.get("item_id")
        else:
            ext_price = None; ext_iid = None
    except:
        ext_price = None; ext_iid = None
    
    print(f"  📦 {cpid} ({len(items)} cuentas nuestras) | ext_cheapest={ext_iid} ${ext_price}")
    
    # Find winner item (Claribel) and others
    winner_item = next((i for i in items if i["account"] == WINNER_ACCOUNT), None)
    other_items = [i for i in items if i["account"] != WINNER_ACCOUNT]
    # Sort other items by STAIRCASE_ORDER
    other_items.sort(key=lambda x: STAIRCASE_ORDER.index(x["account"]) if x["account"] in STAIRCASE_ORDER else 99)
    
    # Calculate winner target
    if winner_item:
        original = max(state["items"].get(winner_item["iid"],{}).get("original_price", winner_item["price"]), winner_item["price"])
        floor = max(FLOOR_OVERRIDES.get(winner_item["iid"], original * DEFAULT_FLOOR_PCT), MIN_FLOOR_PRICE)
        ceiling = CEIL_OVERRIDES.get(winner_item["iid"], original * DEFAULT_CEIL_PCT)
        # GAP agresivo cuando hay competidor en FULL ($80 abajo) para vencer ventaja logística
        effective_gap = 80 if has_full else GAP
        if ext_price is not None:
            winner_target = ext_price - effective_gap
        else:
            winner_target = winner_item["price"]
        winner_target = max(floor, min(ceiling, winner_target))
        winner_target = round(winner_target, 0)
        if has_full:
            print(f"    ⚡ FULL competitor detected — GAP agresivo $80 (vs estándar $10)")
    else:
        # No winner item — choose cheapest external as reference for staircase
        winner_target = ext_price - GAP if ext_price else None
    
    # Apply to winner
    if winner_item and winner_target is not None:
        delta = winner_target - winner_item["price"]
        if abs(delta) >= MIN_DELTA:
            rp = requests.put(f"https://api.mercadolibre.com/items/{winner_item['iid']}", headers=winner_item["H"],
                             json={"price": winner_target}, timeout=15)
            if rp.status_code in (200,201):
                action = "💸 BAJA" if delta < 0 else "📈 SUBE"
                line = f"{action} [{WINNER_ACCOUNT} 🏆] {winner_item['iid']} [{winner_item['title']}] ${int(winner_item['price'])}→${int(winner_target)} (ext ${int(ext_price) if ext_price else '?'})"
                print(f"    {line}")
                if delta < 0: report_down.append(line); total_down += 1
                else: report_up.append(line); total_up += 1
                state["items"][winner_item["iid"]] = {
                    "original_price": original, "floor": floor, "ceiling": ceiling,
                    "last_change_at": now, "role": "winner", "label": winner_item["title"]
                }
            else:
                print(f"    ❌ winner update err {rp.status_code}: {rp.text[:150]}")
        else:
            total_won += 1
            print(f"    ✓ [{WINNER_ACCOUNT} 🏆] {winner_item['iid']} ${int(winner_item['price'])} ya en target")
        time.sleep(0.5)
    
    # Apply staircase to others
    for idx, it in enumerate(other_items):
        if winner_target is None:
            print(f"    ⊘ [{it['account']}] {it['iid']} sin ref — mantener")
            continue
        original = max(state["items"].get(it["iid"],{}).get("original_price", it["price"]), it["price"])
        floor = max(FLOOR_OVERRIDES.get(it["iid"], original * DEFAULT_FLOOR_PCT), MIN_FLOOR_PRICE)
        ceiling = CEIL_OVERRIDES.get(it["iid"], original * DEFAULT_CEIL_PCT)
        # Step (idx+1) above winner
        target = winner_target + (idx + 1) * STAIRCASE_GAP
        target = max(floor, min(ceiling, target))
        target = round(target, 0)
        delta = target - it["price"]
        if abs(delta) < MIN_DELTA:
            total_won += 1
            print(f"    ✓ [{it['account']}] {it['iid']} [{it['title']}] ${int(it['price'])} (escalón {idx+1}, target ${int(target)})")
            continue
        rp = requests.put(f"https://api.mercadolibre.com/items/{it['iid']}", headers=it["H"],
                         json={"price": target}, timeout=15)
        if rp.status_code in (200,201):
            arrow = "💸" if delta < 0 else "📈"
            line = f"{arrow} ESCALÓN {idx+1} [{it['account']}] {it['iid']} [{it['title']}] ${int(it['price'])}→${int(target)}"
            print(f"    {line}")
            report_stair.append(line); total_stair += 1
            state["items"][it["iid"]] = {
                "original_price": original, "floor": floor, "ceiling": ceiling,
                "last_change_at": now, "role": f"step_{idx+1}", "label": it["title"]
            }
        else:
            print(f"    ❌ stair err {rp.status_code}: {rp.text[:150]}")
        time.sleep(0.5)
    print()

state["last_run"] = now
state["winner_account"] = WINNER_ACCOUNT
json.dump(state, open(STATE_FILE,"w"), indent=2)

# Telegram
if TG_TOKEN and TG_CHAT and (report_down or report_up or report_stair):
    lines = [f"⚔️ *Catalog war v4 — Winner: {WINNER_ACCOUNT}*\n"]
    if report_up: lines.append(f"*🏆 Winner subió ({len(report_up)}):*"); lines.extend(report_up[:8])
    if report_down: lines.append(f"\n*🏆 Winner bajó ({len(report_down)}):*"); lines.extend(report_down[:8])
    if report_stair: lines.append(f"\n*Escalonadas ({len(report_stair)}):*"); lines.extend(report_stair[:10])
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id":TG_CHAT,"text":"\n".join(lines)[:4000],"parse_mode":"Markdown"})

print(f"\n=== RESUMEN: 🏆winner_down={total_down} winner_up={total_up} stair={total_stair} ✓no_change={total_won} ===")
