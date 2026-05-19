#!/usr/bin/env python3
"""V4: items fulfillment NO permiten available_quantity en variations.
Probar sin available_quantity."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

WINNER="MLM2886136351"
COLORS_PICS={
  "Morado":["607429-MLM110800675803_042026","914260-MLM109897600830_042026"],
  "Azul":  ["802251-MLM110798835311_042026","943615-MLM110799872413_042026"],
  "Negro": ["743992-MLM110800825777_042026","907793-MLM110799812411_042026","790642-MLM109897660404_042026"],
  "Rojo":  ["754099-MLM110799606261_042026","670337-MLM110799339535_042026","942753-MLM109897720252_042026","872073-MLM109897600822_042026"],
}

variations=[]
for color,pids in COLORS_PICS.items():
    variations.append({
        "attribute_combinations":[{"id":"COLOR","value_name":color}],
        "price":199,
        "picture_ids":pids,
    })

print(f"PUT {WINNER} variations (sin available_quantity, fulfillment)")
r=requests.put(f"{API}/items/{WINNER}",headers=HJ,json={"variations":variations},timeout=30)
print(f"http={r.status_code}")
print(f"body={r.text[:1500]}")
time.sleep(2)
g=requests.get(f"{API}/items/{WINNER}",headers=H,timeout=10).json()
print(f"\npost: variations={len(g.get('variations') or [])}")
for v in (g.get("variations") or []):
    ac=v.get("attribute_combinations",[])
    color=next((a.get("value_name") for a in ac if a.get("id")=="COLOR"),"?")
    print(f"  {v.get('id')} {color}: qty={v.get('available_quantity')} price={v.get('price')} pics={len(v.get('picture_ids') or [])}")
