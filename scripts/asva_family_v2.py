#!/usr/bin/env python3
"""Probar:
1) PUT family_name como field top-level (no como attribute)
2) GET /users/{uid}/user_products para ver si hay endpoint de gestión
3) GET /catalog_products/{id} o similar para Full warehouse merge
"""
import os, requests
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H).json()
uid=me.get("id")
NEW_FAMILY="Bocina Bluetooth Portatil Impermeable Ip67 Bass 35w"

print("=== Probar PUT family_name top-level ===")
for iid in ["MLM2886136351","MLM5233480022","MLM2886030837"]:
    r=requests.put(f"{API}/items/{iid}",headers=HJ,
                   json={"family_name":NEW_FAMILY},timeout=15)
    print(f"  {iid}: http={r.status_code} body={r.text[:300]}")

print("\n=== Sondear endpoints de user_products + variations ===")
for path in [
    f"/users/{uid}/products",
    f"/users/{uid}/user_products",
    f"/users/{uid}/items_groups",
    "/user_products/MLMU3924350282",
    "/user_products/MLMU3924350282/variations",
    "/user_products/MLMU3924350282/items",
    "/catalog_listings/MLM2886136351",
    "/seller_products/MLM2886136351",
]:
    try:
        rr=requests.get(f"{API}{path}",headers=H,timeout=8)
        ct=(rr.text or "")[:200].replace('\n',' ')
        print(f"  GET {path}: {rr.status_code} {ct}")
    except Exception as e:
        print(f"  GET {path}: ERR {e}")

print("\n=== Sondear endpoint para unir user_products ===")
# Probar mover user_product_id de un item al otro
for iid,upid in [("MLM5233480022","MLMU3924350282")]:
    try:
        r=requests.put(f"{API}/items/{iid}",headers=HJ,
                       json={"user_product_id":upid},timeout=15)
        print(f"  {iid} set upid={upid}: http={r.status_code} body={r.text[:300]}")
    except Exception as e:
        print(f"  ERR {e}")
