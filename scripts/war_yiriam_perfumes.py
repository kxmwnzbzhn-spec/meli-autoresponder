#!/usr/bin/env python3
"""War Yiriam perfumes — solo los 12 items clonados que deben ganar buy box vs Wilbert."""
import os,time,requests,json
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"

# Yiriam item → Wilbert item (para ver el precio Wilbert y poner Yiriam = Wilbert - 1)
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
}
MIN_FLOOR=200  # nunca bajar de aquí

def tok():
    return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
T=tok()
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

actions=[]
for yir_id, wb_id in PAIRS.items():
    try:
        yir=requests.get(f"{API}/items/{yir_id}?attributes=id,price,status,sub_status,available_quantity,title",headers=H,timeout=15).json()
        wb=requests.get(f"{API}/items/{wb_id}?attributes=price,status",headers=H,timeout=15).json()
        if yir.get("status")=="paused" and yir.get("available_quantity",0)>0:
            r=requests.put(f"{API}/items/{yir_id}",headers=HJ,json={"status":"active"},timeout=15)
            actions.append(f"REACTIVATE {yir_id} http={r.status_code}")
        wb_price=wb.get("price")
        if not wb_price: continue
        target=max(int(wb_price)-1,MIN_FLOOR)
        yir_price=yir.get("price")
        if yir_price!=target:
            r=requests.put(f"{API}/items/{yir_id}",headers=HJ,json={"price":target},timeout=15)
            actions.append(f"{yir_id} '{(yir.get('title') or '')[:30]}': ${yir_price}→${target} (wb=${wb_price}) http={r.status_code}")
    except Exception as e:
        actions.append(f"ERR {yir_id}: {e}")
    time.sleep(0.3)

print(f"War-yiriam-perfumes run: {len(actions)} acciones")
for a in actions: print(f"  {a}")
