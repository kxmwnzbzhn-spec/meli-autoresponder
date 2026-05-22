"""Clona MLM2940047227 (fresco) + cierra MLM5390346898.
Chequea duplicados del CPID para avisar canibalización."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json(); uid=me.get("id")

# 1) CLONAR MLM2940047227
print("=== CLONAR MLM2940047227 ===")
g=requests.get(f"{API}/items/MLM2940047227",headers=H,timeout=10).json()
cpid=g.get("catalog_product_id"); cat=g.get("category_id"); price=g.get("price"); title=g.get("title")
print(f"  origen: '{title[:40]}' cpid={cpid} cat={cat} price=${price} status={g.get('status')}")

# chequear duplicados activos del mismo CPID en Yiriam
print(f"  --- listings activos Yiriam con cpid {cpid} ---")
dupes=[]
ids=[]; off=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []; ids.extend(res)
    if len(res)<50 or off>500: break
    off+=50
for i in range(0,len(ids),20):
    mg=requests.get(f"{API}/items?ids={','.join(ids[i:i+20])}",headers=H,timeout=15).json()
    for e in mg:
        b=e.get("body") or {}
        if b.get("catalog_product_id")==cpid:
            dupes.append((b.get("id"),b.get("price")))
print(f"    ya activos con este cpid: {dupes}")

payload={"site_id":"MLM","category_id":cat,"price":price or 350,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
    "condition":"new","catalog_product_id":cpid,"catalog_listing":True,"title":title}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"  CLONE http={r.status_code}")
new_id=None
if r.status_code<300:
    new_id=r.json().get("id"); print(f"  NEW: {new_id} ✅ (floor $349)")
else:
    print(f"  body={r.text[:300]}")

# 2) CERRAR MLM5390346898
print("\n=== CERRAR MLM5390346898 ===")
g2=requests.get(f"{API}/items/MLM5390346898",headers=H,timeout=10).json()
print(f"  pre: status={g2.get('status')} price={g2.get('price')}")
if g2.get("status")=="active":
    requests.put(f"{API}/items/MLM5390346898",headers=HJ,json={"status":"paused"},timeout=15); time.sleep(0.4)
rc=requests.put(f"{API}/items/MLM5390346898",headers=HJ,json={"status":"closed"},timeout=15)
print(f"  close http={rc.status_code}")

if new_id: print(f"\nNUEVO_FLOOR_349: \"{new_id}\":349")
