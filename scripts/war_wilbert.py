#!/usr/bin/env python3
"""War-universal for Wilbert — bocinas only, perfumes ignored."""
import os, time, json, requests, re
from datetime import datetime, timezone

API = "https://api.mercadolibre.com"
APP_ID     = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT         = os.environ["MELI_REFRESH_TOKEN_WILBERT"]
TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT    = os.environ.get("TELEGRAM_CHAT_ID")

# Reglas precio por modelo (igual que master playbook)
RULES = {
    "go4":      {"floor": 449, "ceiling": 699,  "rx": r"\bgo\s*4\b"},
    "go3":      {"floor": 399, "ceiling": 599,  "rx": r"\bgo\s*3\b", "force": 499},
    "clip5":    {"floor": 699, "ceiling": 899,  "rx": r"\bclip\s*5\b"},
    "charge6":  {"floor": 399, "ceiling": 999,  "rx": r"\bcharge\s*6\b"},
    "flip7":    {"floor": 399, "ceiling": 999,  "rx": r"\bflip\s*7\b"},
    "grip":     {"floor": 399, "ceiling": 799,  "rx": r"\bgrip\b"},
    "xb100":    {"floor": 299, "ceiling": 599,  "rx": r"xb[\s\-]*100"},
    "bose":     {"floor": 3499, "ceiling": 3499,"rx": r"bose|soundlink"},
}

# Excluir perfumes por keyword en título
PERFUME_RX = re.compile(r"perfume|fragrance|edp|eau de|cologne|alchemia|armaf|odyssey", re.I)
SPEAKER_RX = re.compile(r"bocina|parlante|altavoz|speaker|jbl|bose|sony", re.I)

def refresh():
    r = requests.post(f"{API}/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":RT
    }, timeout=20)
    r.raise_for_status()
    return r.json()["access_token"]

def tg(msg):
    if not TG_TOKEN or not TG_CHAT: return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id":TG_CHAT,"text":msg}, timeout=10)
    except: pass

def classify(title):
    t = title or ""
    if PERFUME_RX.search(t): return None
    for key, r in RULES.items():
        if re.search(r["rx"], t, re.I):
            return key
    return None

def get_user(token):
    return requests.get(f"{API}/users/me", headers={"Authorization":f"Bearer {token}"}, timeout=15).json()

def list_items(token, uid):
    h = {"Authorization":f"Bearer {token}"}
    out = []
    for status in ("active","paused"):
        off = 0
        while True:
            j = requests.get(f"{API}/users/{uid}/items/search?status={status}&limit=50&offset={off}",
                             headers=h, timeout=20).json()
            ids = j.get("results", [])
            if not ids: break
            out += ids
            off += 50
            if off >= j.get("paging",{}).get("total",0): break
    return out

def get_items_bulk(token, ids):
    h={"Authorization":f"Bearer {token}"}
    res={}
    for i in range(0, len(ids), 20):
        chunk = ids[i:i+20]
        r = requests.get(f"{API}/items?ids={','.join(chunk)}&attributes=id,title,price,status,catalog_listing,catalog_product_id,available_quantity",
                         headers=h, timeout=25).json()
        for it in r:
            if it.get("code") == 200:
                b = it.get("body", {})
                res[b.get("id")] = b
    return res

def ptw(token, iid):
    h={"Authorization":f"Bearer {token}"}
    try:
        r = requests.get(f"{API}/items/{iid}/price_to_win?version=v2", headers=h, timeout=15)
        if r.status_code == 200: return r.json()
    except: pass
    return None

def update_price(token, iid, price):
    h={"Authorization":f"Bearer {token}","Content-Type":"application/json"}
    return requests.put(f"{API}/items/{iid}", headers=h, json={"price": price}, timeout=15)

def update_status(token, iid, status):
    h={"Authorization":f"Bearer {token}","Content-Type":"application/json"}
    return requests.put(f"{API}/items/{iid}", headers=h, json={"status": status}, timeout=15)

def relist(token, iid):
    h={"Authorization":f"Bearer {token}","Content-Type":"application/json"}
    return requests.post(f"{API}/items/{iid}/relist", headers=h, json={}, timeout=15)

def main():
    tok = refresh()
    me = get_user(tok)
    uid = me["id"]
    nick = me.get("nickname")
    print(f"Wilbert UID={uid} nick={nick}")

    ids = list_items(tok, uid)
    print(f"Total items en cuenta: {len(ids)}")
    items = get_items_bulk(tok, ids)

    # Filtrar bocinas
    speakers = {}
    for iid, b in items.items():
        title = b.get("title","")
        cat = classify(title)
        if cat:
            speakers[iid] = {**b, "_cat": cat}
    print(f"Bocinas detectadas: {len(speakers)}")

    actions = {"reactivated":0, "relisted":0, "price_down":0, "price_up":0, "no_change":0,
               "floor_block":0, "errors":0, "no_ptw":0}
    log = []

    for iid, it in speakers.items():
        cat = it["_cat"]
        rule = RULES[cat]
        title = it.get("title","")[:50]
        cur_price = it.get("price")
        st = it.get("status")
        cpid = it.get("catalog_product_id")

        # Reactivar si pausado
        if st == "paused":
            if it.get("available_quantity",0) <= 0:
                rr = relist(tok, iid)
                if rr.status_code in (200,201):
                    actions["relisted"] += 1
                    log.append(f"  RELIST {iid} '{title}'")
                    time.sleep(0.3)
                    # refrescar
                    rb = requests.get(f"{API}/items/{iid}", headers={"Authorization":f"Bearer {tok}"}).json()
                    cur_price = rb.get("price")
                else:
                    actions["errors"] += 1
                    log.append(f"  ERR_RELIST {iid} {rr.status_code} {rr.text[:100]}")
                    continue
            else:
                rs = update_status(tok, iid, "active")
                if rs.status_code in (200,201):
                    actions["reactivated"] += 1
                    log.append(f"  ACTIVATE {iid} '{title}'")
                else:
                    actions["errors"] += 1
                    log.append(f"  ERR_ACTIV {iid} {rs.status_code} {rs.text[:100]}")
                    continue

        # Force precio Go 3
        if "force" in rule:
            if cur_price != rule["force"]:
                r = update_price(tok, iid, rule["force"])
                if r.status_code in (200,201):
                    actions["price_down" if rule["force"] < cur_price else "price_up"] += 1
                    log.append(f"  FORCE {iid} {cur_price}→{rule['force']} '{title}'")
                else:
                    actions["errors"] += 1
            continue

        # PTW
        pt = ptw(tok, iid)
        if not pt:
            actions["no_ptw"] += 1
            continue
        ptw_price = pt.get("price_to_win") or pt.get("ptw") or pt.get("price")
        win_status = pt.get("status") or pt.get("competitor_status") or ""
        # Detectar FULL en competidor
        is_full = False
        try:
            comp = pt.get("competitor", {}) or pt.get("buy_box_winner", {}) or {}
            ship = comp.get("shipping", {}) or {}
            ltype = ship.get("logistic_type","")
            if ltype in ("fulfillment","fbm"):
                is_full = True
            if pt.get("buy_box_winner_logistic_type") in ("fulfillment","fbm"):
                is_full = True
        except: pass

        if not ptw_price:
            # Sin competencia → subir hacia ceiling
            target = rule["ceiling"]
            if cur_price < target:
                # subir gradual: max 10% step para no asustar MELI
                new = min(target, int(cur_price * 1.10) + 1)
                r = update_price(tok, iid, new)
                if r.status_code in (200,201):
                    actions["price_up"] += 1
                    log.append(f"  UP_NOCOMP {iid} {cur_price}→{new} (ceiling {target}) '{title}'")
                else:
                    actions["errors"] += 1
            else:
                actions["no_change"] += 1
            continue

        # Hay competencia → bajar a ptw-1 (o ptw-5% si FULL)
        if is_full:
            target = int(ptw_price * 0.95)
        else:
            target = int(ptw_price) - 1

        if target < rule["floor"]:
            actions["floor_block"] += 1
            log.append(f"  FLOOR_BLOCK {iid} ptw={ptw_price} floor={rule['floor']} '{title}' (FULL={is_full})")
            # subir a floor si está debajo
            if cur_price < rule["floor"]:
                update_price(tok, iid, rule["floor"])
                log.append(f"    → ajustado a floor {rule['floor']}")
            continue

        target = min(target, rule["ceiling"])

        if target == cur_price:
            actions["no_change"] += 1
            continue

        r = update_price(tok, iid, target)
        if r.status_code in (200,201):
            if target < cur_price:
                actions["price_down"] += 1
                tag = "DOWN_FULL" if is_full else "DOWN"
            else:
                actions["price_up"] += 1
                tag = "UP"
            log.append(f"  {tag} {iid} {cur_price}→{target} (ptw={ptw_price}) '{title}'")
        else:
            actions["errors"] += 1
            log.append(f"  ERR_PRICE {iid} {r.status_code} {r.text[:100]}")
        time.sleep(0.15)

    print("\n=== RESUMEN ===")
    for k,v in actions.items():
        print(f"  {k:>14}: {v}")
    print("\n=== ACCIONES ===")
    for line in log: print(line)

    # TG resumen corto
    if any(actions[k] for k in ("reactivated","relisted","price_down","price_up","floor_block")):
        msg = (f"⚔️ war-wilbert\n"
               f"react={actions['reactivated']} relist={actions['relisted']} "
               f"↓={actions['price_down']} ↑={actions['price_up']} "
               f"floor={actions['floor_block']} err={actions['errors']}")
        tg(msg)

if __name__ == "__main__":
    main()
