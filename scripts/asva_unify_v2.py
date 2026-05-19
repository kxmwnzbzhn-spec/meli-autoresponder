#!/usr/bin/env python3
"""Retry: NO tocar title (tiene family_name), solo variations.
Investigar errors de close en Negro/Rojo (body completo).
"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

WINNER="MLM2886136351"  # Morado, 27 ventas
COLORS={
  "Morado": "MLM2886136351",
  "Azul":   "MLM5233454100",
  "Negro":  "MLM5233480022",
  "Rojo":   "MLM2886030837",
}

# Get current state + pictures
pics_by_color={}
for color,iid in COLORS.items():
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    pics_by_color[color]=[p.get("id") for p in (g.get("pictures") or [])]
    print(f"{color} {iid}: status={g.get('status')} family={g.get('family_name')} pics={len(pics_by_color[color])}")

variations=[]
for color in ("Morado","Azul","Negro","Rojo"):
    variations.append({
        "attribute_combinations":[{"id":"COLOR","value_name":color}],
        "price":199,
        "available_quantity":1,
        "picture_ids": pics_by_color[color][:6],
    })

print(f"\nPUT {WINNER} con variations (sin title)")
r=requests.put(f"{API}/items/{WINNER}",headers=HJ,json={"variations":variations},timeout=30)
print(f"  http={r.status_code}")
print(f"  body={r.text[:800]}")
time.sleep(2)
g=requests.get(f"{API}/items/{WINNER}",headers=H,timeout=10).json()
print(f"  post: status={g.get('status')} variations={len(g.get('variations') or [])}")
for v in (g.get("variations") or []):
    ac=v.get("attribute_combinations",[])
    color=next((a.get("value_name") for a in ac if a.get("id")=="COLOR"),"?")
    print(f"    {v.get('id')} {color} qty={v.get('available_quantity')} price={v.get('price')} pics={len(v.get('picture_ids') or [])}")

# Cerrar las otras 3 — debug
print(f"\n=== DEBUG CLOSE Negro+Rojo ===")
for color in ("Azul","Negro","Rojo"):
    iid=COLORS[color]
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    print(f"  {iid} ({color}) pre: status={g.get('status')} sub={g.get('sub_status')}")
    rc=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=15)
    print(f"    close http={rc.status_code} body={rc.text[:300]}")
    time.sleep(0.5)
