#!/usr/bin/env python3
"""
Multi-account catalog price war — v2 with fallback when no BBW data.
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

STEP = 10
DEFAULT_FLOOR_PCT = 0.55
FLOOR_OVERRIDES = {}

STATE_FILE = "catalog_war_state.json"
try: state = json.load(open(STATE_FILE))
except: state = {"items": {}, "last_run": 0}

now = int(time.time())
report = []
total_changed = total_won = total_no_data = total_floored = 0

def get_best_competitor(cpid, my_iid, H):
    """Returns (best_price, best_iid) excluding my_iid. None if no data."""
    try:
        # /products/{cpid}/items returns items ordered by relevance (usually buy box first)
        r = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=20", headers=H, timeout=10).json()
    except: return None, None
    items = r.get("results", [])
    competitors = [i for i in items if i.get("item_id") != my_iid]
    if not competitors: return None, None
    # Find cheapest active
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
        
        # 1) Try buy_box_winner first
        try:
            pr = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H, timeout=10).json()
        except: continue
        bbw = pr.get("buy_box_winner") or {}
        bbw_price = bbw.get("price")
        bbw_item = bbw.get("item_id")
        
        # If we ARE the BBW
        if bbw_item == iid:
            total_won += 1
            print(f"    ✅ {iid} [{title}] ${int(our_price)} GANAMOS BBW")
            continue
        
        # 2) Get competitor reference price
        ref_price = None
        ref_source = ""
        if bbw_price is not None and bbw_item != iid:
            ref_price = float(bbw_price)
            ref_source = f"BBW {bbw_item}"
        else:
            comp_price, comp_iid = get_best_competitor(cpid, iid, H)
            if comp_price is not None:
                ref_price = comp_price
                ref_source = f"competitor {comp_iid}"
        
        if ref_price is None:
            total_no_data += 1
            print(f"    ⊘ {iid} [{title}] ${int(our_price)} sin datos competencia")
            continue
        
        # We have reference. Are we cheaper?
        if our_price <= ref_price:
            total_won += 1
            print(f"    ✅ {iid} [{title}] ${int(our_price)} (ref ${int(ref_price)}) ya somos los mejores")
            continue
        
        # We're losing — drop $10 (or to ref-1 if smarter)
        item_state = state["items"].get(iid, {})
        original_price = max(item_state.get("original_price", our_price), our_price)
        floor = FLOOR_OVERRIDES.get(iid, original_price * DEFAULT_FLOOR_PCT)
        
        candidate = our_price - STEP
        if candidate < floor:
            total_floored += 1
            print(f"    🛑 {iid} [{title}] ${int(our_price)} FLOOR ${int(floor)} (ref ${int(ref_price)})")
            state["items"][iid] = {"original_price": original_price, "floor": floor, "label": title}
            continue
        
        target = candidate
        if ref_price - 1 >= floor and ref_price - 1 < candidate:
            target = ref_price - 1
        new_price = round(target, 0)
        
        rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H, json={"price": new_price}, timeout=15)
        if rp.status_code in (200,201):
            total_changed += 1
            msg = f"💸 {label} `{iid}` [{title}] ${int(our_price)}→${int(new_price)} (vs {ref_source} ${int(ref_price)})"
            print(f"    {msg}")
            report.append(msg)
            state["items"][iid] = {"original_price":original_price,"last_drop_at":now,"floor":floor,"last_ref":ref_price,"label":title}
        else:
            print(f"    ❌ {iid} update err {rp.status_code}: {rp.text[:200]}")
        time.sleep(0.5)

state["last_run"] = now
json.dump(state, open(STATE_FILE,"w"), indent=2)

if TG_TOKEN and TG_CHAT and report:
    msg_lines = [f"⚔️ *Catalog war: {total_changed} bajadas*"]
    msg_lines.extend(report[:20])
    if len(report) > 20: msg_lines.append(f"...+{len(report)-20} más")
    msg_lines.append(f"\n✅ Ganamos: {total_won} | 🛑 Floor: {total_floored} | ⊘ Sin datos: {total_no_data}")
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  json={"chat_id":TG_CHAT,"text":"\n".join(msg_lines)[:4000],"parse_mode":"Markdown"})

print(f"\n=== RESUMEN: bajadas={total_changed} ganamos={total_won} floor={total_floored} sin_data={total_no_data} ===")
