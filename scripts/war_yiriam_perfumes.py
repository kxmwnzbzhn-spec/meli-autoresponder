#!/usr/bin/env python3
"""War Yiriam perfumes — user's 12 authoritative IDs."""
import os,time,json,base64,requests
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
MIN_FLOOR=200

# 12 user IDs → Wilbert source (best guess; if not in map use ptw only)
PAIRS={
  "MLM2935286605":"MLM2908818183",  # Angel Nova
  "MLM2935286537":"MLM5309659262",  # Billie Eilish
  "MLM2935286615":"MLM2916649417",  # Jo Milano Spades
  "MLM2935286651":"MLM2916672247",  # Million Gold H
  "MLM2935286681":"MLM2916908753",  # Lattafa Khamrah
  "MLM2935286703":"MLM2916921559",  # Creed Aventus
  "MLM2935298361":"MLM2916700919",  # Dior Sauvage
  "MLM5353104620":"MLM2916908777",  # Orientica Royal Amber (nuevo relist)
  "MLM2935286557":"MLM2908793361",  # Lattafa Confession
  "MLM2935286629":"MLM2916897121",  # Orientica Amber Rouge
  "MLM5353056250":"MLM5265893750",  # Armaf Island Bliss
  "MLM5353056406":"MLM2916676513",  # Lady Million Gold
  "MLM2935447531":"MLM2916921591",
  "MLM2935447545":"MLM2916932945",
  "MLM5353156204":"MLM2916672499",
  "MLM2935587237":"MLM2916921745",
  "MLM2935587247":"MLM2916672931",
  "MLM2935587257":"MLM2916897215",
}

def tok():
    return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
T=tok()
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

acts=[]
for yir_id,wb_id in PAIRS.items():
    yir=requests.get(f"{API}/items/{yir_id}",headers=H,timeout=15).json()
    if not yir.get("id"):
        acts.append(f"SKIP {yir_id} (no data)")
        continue
    wb=requests.get(f"{API}/items/{wb_id}?attributes=price",headers=H,timeout=15).json()
    title=(yir.get("title") or "")[:35]
    cur=yir.get("price")
    status=yir.get("status")
    qty=yir.get("available_quantity",0)
    if status in ("closed",): continue
    if status=="paused":
        body={"status":"active"}
        if qty<=0: body["available_quantity"]=1
        r=requests.put(f"{API}/items/{yir_id}",headers=HJ,json=body,timeout=15)
        acts.append(f"REACTIVATE {yir_id} '{title}' http={r.status_code}")
        if r.status_code<300: status="active"
        time.sleep(0.3)
    if status!="active": continue
    p=requests.get(f"{API}/items/{yir_id}/price_to_win?version=v2",headers=H,timeout=15).json()
    ptw=p.get("price_to_win")
    p_status=p.get("status","")
    wb_price=int(wb.get("price",0) or 0)
    candidates=[]
    if ptw: candidates.append(int(ptw)-1)
    if wb_price>0: candidates.append(wb_price-1)
    if not candidates: continue
    target=max(min(candidates),MIN_FLOOR)
    if target!=cur:
        r=requests.put(f"{API}/items/{yir_id}",headers=HJ,json={"price":target},timeout=15)
        acts.append(f"{yir_id} '{title}' ${cur}→${target} (ptw=${ptw} wb=${wb_price} {p_status}) http={r.status_code}")
    time.sleep(0.3)

print(f"war-yiriam-perfumes: {len(acts)} acciones")
for a in acts: print(f"  {a}")
