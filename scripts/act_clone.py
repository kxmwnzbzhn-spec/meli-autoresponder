import os, requests
import meli_token
API="https://api.mercadolibre.com"
ACT=["MLM2890989209","MLM2890989785","MLM2890989189"]
CLONE_SRC=["MLM2916942827","MLM2950827407","MLM5364336602"]
CT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]).json()["access_token"]
YT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
HC={"Authorization":f"Bearer {CT}"}; HCJ={**HC,"Content-Type":"application/json"}
HY={"Authorization":f"Bearer {YT}"}

print("=== ACTIVAR EN CLARIBEL ===")
for iid in ACT:
    it=requests.get(f"{API}/items/{iid}?attributes=status,available_quantity,title,seller_id",headers=HC,timeout=15).json()
    print(f"  {iid} '{(it.get('title') or '')[:35]}' status={it.get('status')} qty={it.get('available_quantity')}")
    body={"status":"active"}
    if (it.get("available_quantity") or 0)<1: body["available_quantity"]=1
    r=requests.put(f"{API}/items/{iid}",headers=HCJ,json=body,timeout=15)
    f=requests.get(f"{API}/items/{iid}?attributes=status",headers=HC,timeout=15).json()
    print(f"    -> http={r.status_code} status={f.get('status')} {('' if r.status_code<300 else r.text[:200])}")

print("\n=== CLONAR YIRIAM -> CLARIBEL ===")
for src in CLONE_SRC:
    s=requests.get(f"{API}/items/{src}",headers=HY,timeout=20).json()
    cpid=s.get("catalog_product_id"); title=s.get("title"); cat=s.get("category_id")
    price=s.get("price"); lt=s.get("listing_type_id") or "gold_pro"
    print(f"  SRC {src} '{(title or '')[:35]}' cpid={cpid} cat={cat} price={price}")
    if not cpid: print("    SKIP (sin cpid)"); continue
    payload={"site_id":"MLM","title":title,"category_id":cat,
             "catalog_product_id":cpid,"catalog_listing":True,
             "price":price,"currency_id":"MXN","available_quantity":1,
             "buying_mode":"buy_it_now","listing_type_id":lt,"condition":"new"}
    r=requests.post(f"{API}/items",headers=HCJ,json=payload,timeout=40)
    if r.status_code<300:
        j=r.json(); print(f"    NEW {j.get('id')} status={j.get('status')} price={j.get('price')} {j.get('permalink')}")
    else:
        print(f"    ERR http={r.status_code} {r.text[:300]}")
print("\nDONE")
