#!/usr/bin/env python3
"""War-universal for Wilbert v2 — bocinas only.
Lógica corregida:
  - status=winning + competitors_sharing=0 → subir hacia ceiling (10% step)
  - status=sharing → ptw-1 con respeto a floor
  - status=competing/losing → ptw-1 (o ptw*0.95 si FULL)
  - sin ptw → subir hacia ceiling
"""
import os, time, json, requests, re

API = "https://api.mercadolibre.com"
APP_ID     = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT         = os.environ["MELI_REFRESH_TOKEN_WILBERT"]
TG_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT    = os.environ.get("TELEGRAM_CHAT_ID")

RULES = {
    "go4":      {"floor": 449, "ceiling": 699,  "rx": r"\bgo\s*4\b"},
    "go3":      {"floor": 399, "ceiling": 599,  "rx": r"\bgo\s*3\b", "force": 499},
    "clip5":    {"floor": 699, "ceiling": 899,  "rx": r"\bclip\s*5\b"},
    "charge6":  {"floor": 399, "ceiling": 999,  "rx": r"\bcharge\s*6\b"},
    "flip7":    {"floor": 399, "ceiling": 999,  "rx": r"\bflip\s*7\b"},
    "grip":     {"floor": 399, "ceiling": 799,  "rx": r"\bgrip\b"},
    "xb100":    {"floor": 499, "ceiling": 699,  "rx": r"xb[\s\-]*100"},
    "bose":     {"floor": 1999, "ceiling": 3999,"rx": r"bose|soundlink"},
}
PERFUME_RX = re.compile(r"perfume|fragrance|edp|eau de|cologne|alchemia|armaf|odyssey", re.I)
UP_STEP_PCT = 0.05  # +10% por corrida cuando solos
MAX_UP = 30         # tope de subida por corrida ($)

def refresh():
    r = requests.post(f"{API}/oauth/token", data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":RT}, timeout=20)
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
        if re.search(r["rx"], t, re.I): return key
    return None

def list_items(token, uid):
    h={"Authorization":f"Bearer {token}"}
    out=[]
    for status in ("active","paused"):
        off=0
        while True:
            j=requests.get(f"{API}/users/{uid}/items/search?status={status}&limit=50&offset={off}",
                           headers=h, timeout=20).json()
            ids=j.get("results",[])
            if not ids: break
            out += ids
            off += 50
            if off >= j.get("paging",{}).get("total",0): break
    return out

def get_items_bulk(token, ids):
    h={"Authorization":f"Bearer {token}"}; res={}
    for i in range(0,len(ids),20):
        chunk=ids[i:i+20]
        r=requests.get(f"{API}/items?ids={','.join(chunk)}&attributes=id,title,price,status,catalog_listing,catalog_product_id,available_quantity",
                       headers=h, timeout=25).json()
        for it in r:
            if it.get("code")==200:
                b=it.get("body",{}); res[b.get("id")]=b
    return res

def ptw(token, iid):
    try:
        r=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",
                       headers={"Authorization":f"Bearer {token}"}, timeout=15)
        if r.status_code==200: return r.json()
    except: pass
    return None

def update_price(token, iid, price):
    return requests.put(f"{API}/items/{iid}",
        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
        json={"price": price}, timeout=15)

def update_status(token, iid, status):
    return requests.put(f"{API}/items/{iid}",
        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
        json={"status": status}, timeout=15)

def update_qty_active(token, iid, qty=1):
    return requests.put(f"{API}/items/{iid}",
        headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
        json={"available_quantity": qty, "status": "active"}, timeout=15)

def main():
    tok = refresh()
    me = requests.get(f"{API}/users/me", headers={"Authorization":f"Bearer {tok}"}, timeout=15).json()
    uid = me["id"]
    print(f"Wilbert UID={uid} nick={me.get('nickname')}")

    ids = list_items(tok, uid)
    print(f"Total items: {len(ids)}")
    items = get_items_bulk(tok, ids)
    speakers = {iid:{**b,"_cat":classify(b.get('title',''))} for iid,b in items.items() if classify(b.get('title',''))}
    print(f"Bocinas: {len(speakers)}")

    A={"reactivated":0,"price_down":0,"price_up":0,"no_change":0,
       "floor_block":0,"errors":0,"no_ptw":0,"winning_alone":0,"sharing":0}
    log=[]

    for iid, it in speakers.items():
        cat=it["_cat"]; rule=RULES[cat]
        title=it.get("title","")[:48]
        cur=it.get("price"); st=it.get("status"); qty=it.get("available_quantity",0)

        # Reactivar pausados
        if st=="paused":
            if qty<=0:
                r=update_qty_active(tok, iid, 1)
            else:
                r=update_status(tok, iid, "active")
            if r.status_code in (200,201):
                A["reactivated"]+=1
                log.append(f"  ACTIVATE {iid} '{title}'")
                cur = it.get("price")
            else:
                A["errors"]+=1
                log.append(f"  ERR_ACTIV {iid} {r.status_code} {r.text[:80]}")
                continue

        # Force Go 3
        if "force" in rule:
            if cur != rule["force"]:
                r=update_price(tok, iid, rule["force"])
                if r.status_code in (200,201):
                    k = "price_up" if rule["force"]>cur else "price_down"
                    A[k]+=1
                    log.append(f"  FORCE {iid} {cur}→{rule['force']} '{title}'")
                else: A["errors"]+=1
            continue

        pt = ptw(tok, iid)
        if not pt:
            A["no_ptw"]+=1
            continue

        ptw_price = pt.get("price_to_win")
        status = pt.get("status","")
        sharing_n = pt.get("competitors_sharing_first_place", 0)
        # Detect FULL del winner
        is_full=False
        winner = pt.get("winner") or {}
        for b in winner.get("boosts", []):
            if b.get("id")=="fulfillment" and b.get("status")=="boosted":
                is_full=True; break

        target = None
        tag = ""

        if status == "winning" and sharing_n == 0:
            # Solos ganando — subir hacia ceiling
            A["winning_alone"]+=1
            step = min(MAX_UP, max(1, int(cur * UP_STEP_PCT)))
            target = min(rule["ceiling"], cur + step)
            tag = "UP_ALONE"
            if target == cur:
                A["no_change"]+=1
                continue
        elif status == "sharing" or (status=="winning" and sharing_n>0):
            # Empate — bajar 1 peso para tomar single buy box
            A["sharing"]+=1
            target = (ptw_price or cur) - 1
            tag = "DOWN_BREAK_TIE"
            if target < rule["floor"]:
                A["floor_block"]+=1
                log.append(f"  FLOOR_BLOCK {iid} ptw={ptw_price} floor={rule['floor']} '{title}'")
                if cur < rule["floor"]:
                    update_price(tok, iid, rule["floor"])
                continue
        else:
            # competing/losing/sharing_first_place perdiendo
            if not ptw_price:
                # sin ptw, subir
                step = min(MAX_UP, max(1, int(cur * UP_STEP_PCT)))
                target = min(rule["ceiling"], cur + step)
                tag = "UP_NOPTW"
            else:
                if is_full:
                    target = int(ptw_price * 0.95)
                    tag = "DOWN_FULL"
                else:
                    target = int(ptw_price) - 1
                    tag = "DOWN"
                if target < rule["floor"]:
                    A["floor_block"]+=1
                    log.append(f"  FLOOR_BLOCK {iid} ptw={ptw_price} floor={rule['floor']} (FULL={is_full}) '{title}'")
                    if cur < rule["floor"]:
                        update_price(tok, iid, rule["floor"])
                    continue

        target = min(target, rule["ceiling"])
        target = max(target, rule["floor"])

        if target == cur:
            A["no_change"]+=1
            continue

        r = update_price(tok, iid, target)
        if r.status_code in (200,201):
            if target > cur: A["price_up"]+=1
            else: A["price_down"]+=1
            log.append(f"  {tag} {iid} {cur}→{target} (ptw={ptw_price} st={status} sh={sharing_n} FULL={is_full}) '{title}'")
        else:
            A["errors"]+=1
            log.append(f"  ERR_PRICE {iid} {r.status_code} {r.text[:80]}")
        time.sleep(0.12)

    print("\n=== RESUMEN ===")
    for k,v in A.items(): print(f"  {k:>14}: {v}")
    print("\n=== ACCIONES ===")
    for l in log: print(l)

    if any(A[k] for k in ("reactivated","price_down","price_up","floor_block")):
        msg=(f"⚔️ war-wilbert v2\n"
             f"react={A['reactivated']} ↑={A['price_up']} ↓={A['price_down']} "
             f"alone={A['winning_alone']} share={A['sharing']} "
             f"floor={A['floor_block']} err={A['errors']}")
        tg(msg)

if __name__ == "__main__":
    main()
