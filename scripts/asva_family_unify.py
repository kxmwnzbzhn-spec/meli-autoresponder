#!/usr/bin/env python3
"""Unificar 4 listings via FAMILY_NAME compartido.
Currently each tiene un family_name distinto (con color al final).
Si los 4 comparten EL MISMO family_name → MELI los muestra como variantes del mismo producto.
También probamos endpoint /items/{id}/families o /products/families si existe.
"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# Reactivar Azul primero (lo cerramos antes — revertirlo si se puede)
print("=== Restaurar Azul si se puede ===")
r=requests.put(f"{API}/items/MLM5233454100",headers=HJ,json={"status":"paused"},timeout=15)
print(f"  azul un-close: http={r.status_code} body={r.text[:200]}")
time.sleep(1)

# Diagnóstico: ¿qué endpoints de family existen?
print("\n=== Diagnóstico endpoints family ===")
for path in [
    "/items/MLM2886136351/families",
    "/items/MLM2886136351/family",
    "/families",
    "/users/me/items_families",
    "/seller_promotions/families",
]:
    try:
        rr=requests.get(f"{API}{path}",headers=H,timeout=8)
        print(f"  GET {path}: {rr.status_code}")
        if rr.status_code<300:
            print(f"    body={rr.text[:300]}")
    except Exception as e:
        print(f"  GET {path}: ERR {e}")

ITEMS=["MLM2886136351","MLM5233454100","MLM5233480022","MLM2886030837"]
NEW_FAMILY="Bocina Bluetooth Portatil Impermeable Ip67 Bass 35w"

print(f"\n=== Estado actual family_name ===")
for iid in ITEMS:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    print(f"  {iid} family='{g.get('family_name')}' inv='{g.get('inventory_id')}' user_product_id='{g.get('user_product_id')}'")
    # check attributes for FAMILY_NAME
    for a in g.get("attributes") or []:
        if a.get("id") in ("FAMILY_NAME","MODEL","LINE","COLOR"):
            print(f"    attr {a.get('id')}={a.get('value_name')}")

# Probar PUT family_name compartido
print(f"\n=== PUT family_name='{NEW_FAMILY}' a los 4 ===")
for iid in ITEMS:
    try:
        # Probar via attribute (preferred way)
        r=requests.put(f"{API}/items/{iid}",headers=HJ,
                       json={"attributes":[{"id":"FAMILY_NAME","value_name":NEW_FAMILY}]},timeout=15)
        print(f"  {iid} attr FAMILY_NAME: http={r.status_code} body={r.text[:200]}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  {iid}: ERR {e}")

time.sleep(2)
print(f"\n=== Estado post-PUT ===")
for iid in ITEMS:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    print(f"  {iid} family='{g.get('family_name')}'")
