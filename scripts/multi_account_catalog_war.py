#!/usr/bin/env python3
"""
Multi-account catalog price war v3:
- LOWERS price when losing (drops $10 toward competitor - $1)
- RAISES price when winning by margin > $10 (sets to competitor - $10 to maximize margin)
- Floor: 55% of original price (no bajar de aquí)
- Ceiling: 130% of original price (no subir de aquí)
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

GAP = 10                    # quedar siempre $10 abajo del competidor más barato
DEFAULT_FLOOR_PCT = 0.55    # floor = 55% del precio original
DEFAULT_CEIL_PCT  = 1.30    # techo = 130% del precio original
MIN_RAISE_DELTA = 5         # solo subir si la subida es ≥ $5 (evita spam)

FLOOR_OVERRIDES = {}
CEIL_OVERRIDES = {}

STATE_FILE = "catalog_war_state.json"
try: state = json.load(open(STATE_FILE))
except: state = {"items": {}, "last_run": 0}

now = int(time.time())
report_down = []  # bajadas
report_up = []    # subidas
total_down = total_up = total_won = total_no_data = total_floored = total_ceiled = 0

def get_best_competitor(cpid, my_iid, H):
    try:
        r = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=20", headers=H, timeout=10).json()
    except: return None, None
    competitors = [i for i in r.get("results",[]) if i.get("item_id") != my_iid]
    if not competitors: return None, None
    cheapest = min(competitors, key=lambda x: float(x.get("price") or 999999))
    p = cheapest.get("price")
    if p is None: return None, None
    return float(p), cheapest.get("item_id")

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
        print(f"[{label}] auth err: {e}"); continue

    print(f"\n=== {label} ({me.get('nickname')}) ===")
    
    item_ids = []
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}", headers=H, timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        item_ids.extend(b); offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break
    
    catalog_items = []
    for iid in item_ids:
        try:
            it = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,catalog_product_id,catalog_listing,status", headers=H, timeout=10).json()
        except: continue
        if it.get("catalog_listing") and it.get("catalog_product_id") and it.get("status")=="active":
            catalog_items.append(it)
    print(f"  Catalog listings activos: {len(catalog_items)}")
    
    for it in catalog_items:
        iid = it["id"]
        cpid = it["catalog_product_id"]
        title = (it.get("title") or "")[:35]
        our_price = float(it.get("price") or 0)
        if our_price <= 0: continue
        
        # Find reference: prefer cheapest competitor (strategic — siempre quedar $GAP debajo del más barato)
        ref_price, ref_iid = get_best_competitor(cpid, iid, H)
        if ref_price is None:
            # Try BBW
            try:
                pr = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H, timeout=10).json()
                bbw = pr.get("buy_box_winner") or {}
                if bbw.get("price") and bbw.get("item_id") != iid:
                    ref_price = float(bbw["price"])
                    ref_iid = bbw.get("item_id")
            except: pass
        
        if ref_price is None:
            total_no_data += 1
            print(f"    ⊘ {iid} [{title}] ${int(our_price)} sin datos competencia")
            continue
        
        item_state = state["items"].get(iid, {})
        original_price = max(item_state.get("original_price", our_price), our_price)
        floor = FLOOR_OVERRIDES.get(iid, original_price * DEFAULT_FLOOR_PCT)
        ceiling = CEIL_OVERRIDES.get(iid, original_price * DEFAULT_CEIL_PCT)
        
        # TARGET = competidor más barato - $GAP
        target = ref_price - GAP
        # Clamp entre floor y ceiling
        if target < floor:
            target = floor
            total_floored += 1
        if target > ceiling:
            target = ceiling
            total_ceiled += 1
        
        new_price = round(target, 0)
        delta = new_price - our_price
        
        if abs(delta) < 1:
            total_won += 1
            print(f"    ✓ {iid} [{title}] ${int(our_price)} ya en target (ref ${int(ref_price)})")
            continue
        
        if delta < 0:
            # Bajamos
            print(f"    💸 BAJA {iid} [{title}] ${int(our_price)}→${int(new_price)} (ref ${int(ref_price)})")
        else:
            # Subimos
            if delta < MIN_RAISE_DELTA:
                # micro-bump no vale la pena
                total_won += 1
                print(f"    ✓ {iid} [{title}] ${int(our_price)} subida muy chica (+${int(delta)})")
                continue
            print(f"    📈 SUBE {iid} [{title}] ${int(our_price)}→${int(new_price)} (ref ${int(ref_price)})")
        
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"price": new_price}, timeout=15)
        if rp.status_code in (200,201):
            line = f"`{iid}` [{title}] ${int(our_price)}→${int(new_price)} (vs ${int(ref_price)})"
            if delta < 0:
                total_down += 1
                report_down.append(f"💸 {label} {line}")
            else:
                total_up += 1
                report_up.append(f"📈 {label} {line}")
            state["items"][iid] = {
                "original_price": original_price, "floor": floor, "ceiling": ceiling,
                "last_change_at": now, "last_ref": ref_price, "label": title,
                "last_action": "down" if delta<0 else "up"
            }
        else:
            print(f"    ❌ update err {rp.status_code}: {rp.text[:200]}")
        time.sleep(0.5)

state["last_run"] = now
json.dump(state, open(STATE_FILE,"w"), indent=2)

# Telegram report
if TG_TOKEN and TG_CHAT and (report_down or report_up):
    lines = [f"⚔️ *Catalog war: {total_down} 💸 bajadas, {total_up} 📈 subidas*\n"]
    if report_up:
        lines.append("*Subidas (margen ↑):*")
        lines.extend(report_up[:15])
    if report_down:
        lines.append("\n*Bajadas (defensa):*")
        lines.extend(report_down[:15])
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id":TG_CHAT,"text":"\n".join(lines)[:4000],"parse_mode":"Markdown"})

print(f"\n=== RESUMEN: 💸{total_down} 📈{total_up} ✓{total_won} 🛑floor={total_floored} ⊘{total_no_data} ===")
