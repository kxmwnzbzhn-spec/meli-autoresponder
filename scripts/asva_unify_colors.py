#!/usr/bin/env python3
"""Unificar 4 listings ASVA (4 colores) en uno solo con variantes.
Winner: MLM2886136351 (Morado, 27 ventas).
"""
import os, requests, json, time
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

# Inspeccionar los 4
info={}
for color, iid in COLORS.items():
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    info[color]={
      "id": iid,
      "status": g.get("status"),
      "sub_status": g.get("sub_status"),
      "qty": g.get("available_quantity"),
      "price": g.get("price"),
      "title": g.get("title"),
      "category_id": g.get("category_id"),
      "pictures": [p.get("id") for p in (g.get("pictures") or [])],
      "attributes": g.get("attributes") or [],
      "variations": g.get("variations") or [],
      "listing_type": g.get("listing_type_id"),
    }
    print(f"--- {color} {iid} ---")
    print(f"  status={info[color]['status']} qty={info[color]['qty']} price={info[color]['price']}")
    print(f"  pics={len(info[color]['pictures'])}")
    print(f"  variations={len(info[color]['variations'])}")
    print(f"  title='{info[color]['title']}'")

print("\n=== INFO COLECTADA. Construyendo variations payload ===")

# Build variations
variations=[]
for color in ("Morado","Azul","Negro","Rojo"):
    pics=info[color]["pictures"][:6]  # max 6 por variation suele bastar
    variations.append({
        "attribute_combinations": [
            {"id":"COLOR","value_name":color}
        ],
        "price": 199,
        "available_quantity": 1,
        "sold_quantity": 0,  # MELI lo maneja
        "picture_ids": pics,
    })

# PUT al winner — actualizar título limpio + variations
# El title actual es "Bocina Bluetooth Portatil Impermeable Ip67 Bass 35w Morado Morado"
# Limpio: "Bocina Bluetooth Portátil Impermeable Ip67 Bass 35w" (50 chars)
new_title="Bocina Bluetooth Portátil Impermeable Ip67 Bass 35w"

payload={
    "title": new_title,
    "variations": variations,
}

print(f"\nPayload variations (cantidad={len(variations)}):")
for v in variations:
    print(f"  {v['attribute_combinations'][0]['value_name']:<8} pics={len(v['picture_ids'])} price={v['price']} qty={v['available_quantity']}")

print(f"\nPUT {WINNER} ...")
r=requests.put(f"{API}/items/{WINNER}",headers=HJ,json=payload,timeout=30)
print(f"  http={r.status_code}")
if r.status_code>=300:
    print(f"  body={r.text[:600]}")
else:
    g2=requests.get(f"{API}/items/{WINNER}",headers=H,timeout=10).json()
    print(f"  post: variations={len(g2.get('variations') or [])}")
    for v in (g2.get("variations") or []):
        ac=v.get("attribute_combinations",[])
        color=next((a.get("value_name") for a in ac if a.get("id")=="COLOR"),"?")
        print(f"    {v.get('id')} {color} qty={v.get('available_quantity')} price={v.get('price')}")

# Cerrar las otras 3
print(f"\n=== CERRAR LAS OTRAS 3 ===")
for color,iid in COLORS.items():
    if iid==WINNER: continue
    # Ya están paused, ahora close
    rc=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=15)
    print(f"  {iid} ({color}) close http={rc.status_code}")
    time.sleep(0.3)
