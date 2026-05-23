#!/usr/bin/env python3
"""Recorre cada cuenta, busca items en blacklist y los pausa.
Si el item no es del seller actual, lo ignora (no es nuestro)."""
import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]

ACCOUNTS={
 "JUAN":"MELI_REFRESH_TOKEN","RAYMUNDO":"MELI_REFRESH_TOKEN_RAYMUNDO",
 "CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL","ASVA":"MELI_REFRESH_TOKEN_ASVA",
 "DILCIE":"MELI_REFRESH_TOKEN_DILCIE","MILDRED":"MELI_REFRESH_TOKEN_MILDRED",
 "BREN":"MELI_REFRESH_TOKEN_BREN","WILBERT":"MELI_REFRESH_TOKEN_WILBERT",
 "YC_NEW":"MELI_REFRESH_TOKEN_YC_NEW",
}

with open("blacklist.json") as f:
    bl=json.load(f)
ITEMS=[x["item_id"] for x in bl.get("items",[])]
print(f"Blacklist: {ITEMS}")

def refresh(rt):
    try:
        r=meli_token.refresh(rt)
        return r.json().get("access_token")
    except: return None

found_log=[]
for acc, envk in ACCOUNTS.items():
    rt=os.environ.get(envk)
    if not rt: 
        print(f"[{acc}] sin token, skip")
        continue
    tok=refresh(rt)
    if not tok:
        print(f"[{acc}] refresh failed")
        continue
    h={"Authorization":f"Bearer {tok}"}
    me=requests.get(f"{API}/users/me",headers=h,timeout=15).json()
    uid=me.get("id")
    if not uid:
        print(f"[{acc}] no uid")
        continue
    for iid in ITEMS:
        try:
            it=requests.get(f"{API}/items/{iid}",headers=h,timeout=15).json()
            seller=it.get("seller_id")
            if seller!=uid: continue
            st=it.get("status")
            print(f"[{acc}] OWNS {iid} status={st} title='{it.get('title','')[:50]}'")
            if st=="active":
                hj={**h,"Content-Type":"application/json"}
                r=requests.put(f"{API}/items/{iid}",headers=hj,
                    json={"status":"paused"},timeout=15)
                print(f"  PAUSE: {r.status_code}")
                found_log.append(f"{acc}/{iid} paused")
            else:
                found_log.append(f"{acc}/{iid} already {st}")
        except Exception as e:
            print(f"[{acc}] error {iid}: {e}")

print("\n=== SUMMARY ===")
for l in found_log: print(l)
