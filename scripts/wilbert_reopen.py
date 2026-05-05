#!/usr/bin/env python3
"""Wilbert morning reopen — idempotente.
1) Re-enable war_wilbert.yml + war_wilbert_perfumes.yml
2) Reactivar items pausados (status=active, qty=1) excluyendo blacklist
3) Tolera errores y reintenta items con problemas
4) Reporta TG resumen
"""
import os, time, json, requests
API="https://api.mercadolibre.com"
APP_ID=os.environ["MELI_APP_ID"]
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
GH_TOKEN=os.environ["GH_TOKEN_OPS"]
OWNER=os.environ.get("REPO_OWNER","kxmwnzbzhn-spec")
REPO="meli-autoresponder"
TG_TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN")
TG_CHAT=os.environ.get("TELEGRAM_CHAT_ID")

def tg(m):
    if TG_TOKEN and TG_CHAT:
        try: requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id":TG_CHAT,"text":m},timeout=8)
        except: pass

def gh(method, path, **kw):
    h={"Authorization":f"Bearer {GH_TOKEN}","Accept":"application/vnd.github+json"}
    return requests.request(method, f"https://api.github.com{path}", headers=h, timeout=20, **kw)

# 1) Cargar blacklist
try:
    BL=set(x["item_id"] for x in json.load(open("blacklist.json")).get("items",[]))
except: BL=set()
print(f"Blacklist: {BL}")

# 2) Enable workflows war_wilbert.yml + war_wilbert_perfumes.yml
TARGETS=["war_wilbert.yml","war_wilbert_perfumes.yml"]
for p in (1,2,3,4):
    r=gh("GET",f"/repos/{OWNER}/{REPO}/actions/workflows?per_page=100&page={p}").json()
    for w in r.get("workflows",[]):
        fn=w["path"].split("/")[-1]
        if fn in TARGETS:
            wid=w["id"]; state=w["state"]
            if state!="active":
                er=gh("PUT",f"/repos/{OWNER}/{REPO}/actions/workflows/{wid}/enable")
                print(f"  enable {fn}: {er.status_code}")
            else:
                print(f"  {fn} already active")

# 3) Refresh MELI token + reactivar items
def meli_refresh():
    r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
        "client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=20)
    return r.json()["access_token"]

tok=meli_refresh()
h={"Authorization":f"Bearer {tok}"}
hj={**h,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=h,timeout=15).json()
uid=me["id"]
print(f"Wilbert UID={uid}")

# Listar paused
ids=[]
off=0
while True:
    j=requests.get(f"{API}/users/{uid}/items/search?status=paused&limit=50&offset={off}",headers=h,timeout=20).json()
    r=j.get("results",[]); ids+=r
    off+=50
    if off>=j.get("paging",{}).get("total",0) or not r: break
print(f"Paused items: {len(ids)}")

reactivated=0; skipped_bl=0; errors=0
err_log=[]

for iid in ids:
    if iid in BL:
        skipped_bl+=1
        continue
    # 1er intento: status=active + qty=1
    r=requests.put(f"{API}/items/{iid}",headers=hj,json={"status":"active","available_quantity":1},timeout=15)
    if r.status_code in (200,201):
        reactivated+=1
    else:
        # retry 2: solo status
        time.sleep(0.3)
        r2=requests.put(f"{API}/items/{iid}",headers=hj,json={"status":"active"},timeout=15)
        if r2.status_code in (200,201):
            reactivated+=1
        else:
            errors+=1
            err_log.append(f"  {iid}: {r.status_code}/{r2.status_code} {r2.text[:120]}")
    time.sleep(0.1)

print(f"\n=== RESUMEN ===")
print(f"  reactivated: {reactivated}")
print(f"  blacklist_skipped: {skipped_bl}")
print(f"  errors: {errors}")
for e in err_log[:10]: print(e)

# 4) Disparar war_wilbert + war_wilbert_perfumes para arrancar el loop
for fn in TARGETS:
    er=gh("POST",f"/repos/{OWNER}/{REPO}/actions/workflows/{fn}/dispatches", json={"ref":"main"})
    print(f"  dispatch {fn}: {er.status_code}")

tg(f"☀️ Wilbert REOPEN 6 AM\n"
   f"reactivados={reactivated} bl_skip={skipped_bl} err={errors}\n"
   f"war_wilbert + perfumes ENABLED + dispatched")
