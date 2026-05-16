#!/usr/bin/env python3
"""War Yiriam perfumes — competir vs externos con PTW + asegurar buy box vs Wilbert."""
import os,time,requests,json
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
MIN_FLOOR=200

PAIRS={
  "MLM5353056250":"MLM5265893750",
  "MLM2935286537":"MLM5309659262",
  "MLM2935286557":"MLM2908793361",
  "MLM5353056302":"MLM2916649417",
  "MLM2935286581":"MLM2916897121",
  "MLM2935286605":"MLM2908818183",
  "MLM2935274091":"MLM2916908777",
  "MLM2935286651":"MLM2916672247",
  "MLM5353056406":"MLM2916676513",
  "MLM2935286681":"MLM2916908753",
  "MLM2935286703":"MLM2916921559",
  "MLM2935298361":"MLM2916700919",
}

def tok():
    return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
T=tok()
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

acts=[]
for yir_id,wb_id in PAIRS.items():
    yir=requests.get(f"{API}/items/{yir_id}",headers=H,timeout=15).json()
    wb=requests.get(f"{API}/items/{wb_id}?attributes=price",headers=H,timeout=15).json()
    title=(yir.get("title") or "")[:35]
    cur=yir.get("price")
    status=yir.get("status")
    qty=yir.get("available_quantity",0)
    sub=yir.get("sub_status",[])

    # 1. Reactivate if paused
    if status=="paused":
        body={"status":"active"}
        if qty<=0: body["available_quantity"]=1
        r=requests.put(f"{API}/items/{yir_id}",headers=HJ,json=body,timeout=15)
        acts.append(f"REACTIVATE {yir_id} '{title}' http={r.status_code}")
        if r.status_code<300: status="active"; cur=yir.get("price")
        time.sleep(0.3)

    if status!="active": continue

    # 2. Get PTW
    p=requests.get(f"{API}/items/{yir_id}/price_to_win?version=v2",headers=H,timeout=15).json()
    ptw=p.get("price_to_win")
    p_status=p.get("status","")
    wb_price=int(wb.get("price",0) or 0)

    # 3. Decide target
    # Target = min(ptw-1, wb_price-1), respetando MIN_FLOOR
    candidates=[]
    if ptw: candidates.append(int(ptw)-1)
    if wb_price>0: candidates.append(wb_price-1)
    if not candidates: continue
    target=max(min(candidates),MIN_FLOOR)
    
    if target!=cur:
        r=requests.put(f"{API}/items/{yir_id}",headers=HJ,json={"price":target},timeout=15)
        acts.append(f"{yir_id} '{title}' ${cur}→${target} (ptw=${ptw} wb=${wb_price} status={p_status}) http={r.status_code}")
    else:
        acts.append(f"{yir_id} '{title}' ${cur}=optimo (ptw=${ptw} wb=${wb_price} status={p_status})")
    time.sleep(0.3)

print(f"war-yiriam-perfumes: {len(acts)} acciones")
for a in acts: print(f"  {a}")
