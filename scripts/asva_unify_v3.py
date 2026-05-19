#!/usr/bin/env python3
"""V3: PUT pictures top-level con union de las 4 listings, luego variations.
Negro/Rojo se quedan paused (no se pueden cerrar — fulfillment stock)."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

WINNER="MLM2886136351"  # Morado
COLORS={
  "Morado": "MLM2886136351",
  "Azul":   "MLM5233454100",
  "Negro":  "MLM5233480022",
  "Rojo":   "MLM2886030837",
}

# Recolectar pictures por color
pics_by_color={}
all_pic_ids=[]
seen=set()
for color,iid in COLORS.items():
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    pids=[p.get("id") for p in (g.get("pictures") or [])]
    pics_by_color[color]=pids
    for pid in pids:
        if pid not in seen:
            seen.add(pid); all_pic_ids.append(pid)
    print(f"{color}: {len(pids)} pics → {pids}")

print(f"\nUNION pictures: {len(all_pic_ids)}")
# MELI permite hasta 12 pictures top-level. Si son más, truncar
top_pics=all_pic_ids[:12]

# Step 1: PUT pictures top-level
print(f"\nPUT pictures top-level ({len(top_pics)})")
r1=requests.put(f"{API}/items/{WINNER}",headers=HJ,
                json={"pictures":[{"id":pid} for pid in top_pics]},timeout=30)
print(f"  http={r1.status_code} body={r1.text[:300]}")
time.sleep(2)

# Re-leer para confirmar
g2=requests.get(f"{API}/items/{WINNER}",headers=H,timeout=10).json()
actual_pics=[p.get("id") for p in (g2.get("pictures") or [])]
print(f"  post: pics={len(actual_pics)} → {actual_pics}")

# Step 2: PUT variations using picture_ids that ARE in actual_pics
print(f"\nPUT variations")
variations=[]
for color in ("Morado","Azul","Negro","Rojo"):
    # Filtrar solo pics que están en top-level
    valid=[p for p in pics_by_color[color] if p in actual_pics][:4]
    if not valid:
        valid=actual_pics[:1]  # fallback
    variations.append({
        "attribute_combinations":[{"id":"COLOR","value_name":color}],
        "price":199,
        "available_quantity":1,
        "picture_ids":valid,
    })
    print(f"  variation {color}: pics={valid}")

r2=requests.put(f"{API}/items/{WINNER}",headers=HJ,json={"variations":variations},timeout=30)
print(f"  http={r2.status_code} body={r2.text[:500]}")
time.sleep(2)

g3=requests.get(f"{API}/items/{WINNER}",headers=H,timeout=10).json()
print(f"\nPOST FINAL: variations={len(g3.get('variations') or [])}")
for v in (g3.get("variations") or []):
    ac=v.get("attribute_combinations",[])
    color=next((a.get("value_name") for a in ac if a.get("id")=="COLOR"),"?")
    print(f"  {v.get('id')} {color} qty={v.get('available_quantity')} price={v.get('price')} pics={len(v.get('picture_ids') or [])}")
