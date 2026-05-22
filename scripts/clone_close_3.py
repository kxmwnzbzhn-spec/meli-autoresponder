"""Pausa+cierra 3 items atorados y los re-publica frescos como catalog listing.
Origen: MLM5363023022 (Go4), MLM2940047227 (Go3 floor349), MLM5363034834 (Go3 floor349)"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

OLD=["MLM5363023022","MLM2940047227","MLM5363034834"]
new_map={}
for iid in OLD:
    print(f"\n=== {iid} ===")
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    cpid=g.get("catalog_product_id"); cat=g.get("category_id"); price=g.get("price")
    title=g.get("title"); print(f"  origen: '{title[:40]}' cpid={cpid} cat={cat} price=${price}")
    # 1) Crear clon nuevo (catalog listing, sin title -> MELI hereda)
    payload={
        "site_id":"MLM","category_id":cat,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
        "condition":"new","catalog_product_id":cpid,"catalog_listing":True,
    }
    r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
    print(f"  CLONE http={r.status_code}")
    if r.status_code<300:
        nid=r.json().get("id")
        new_map[iid]=nid
        print(f"  NEW: {nid} ✅")
    else:
        print(f"  body={r.text[:300]}")
        # reintento sin title ya está; probar con title
        payload["title"]=title
        r2=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
        print(f"  retry con title http={r2.status_code}")
        if r2.status_code<300:
            nid=r2.json().get("id"); new_map[iid]=nid; print(f"  NEW: {nid} ✅")
        else:
            print(f"  body2={r2.text[:300]}")
    time.sleep(1)
    # 2) Cerrar viejo
    if g.get("status")=="active":
        requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15); time.sleep(0.4)
    rc=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=15)
    print(f"  CLOSE old {iid} http={rc.status_code}")
    time.sleep(0.5)

print("\n=== MAPEO viejo→nuevo ===")
for o,n in new_map.items():
    print(f"  {o} → {n}")
# Floors a portar: 2940047227 y 5363034834 = $349
print("\n=== FLOORS NUEVOS ($349) ===")
for o in ["MLM2940047227","MLM5363034834"]:
    if o in new_map: print(f'  "{new_map[o]}":349,')
