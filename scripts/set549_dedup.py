import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json(); uid=me.get("id")

NINE=["MLM5291785036","MLM5291774150","MLM2909183147","MLM2950827385","MLM5390371996",
"MLM2950790153","MLM2950790159","MLM2950790163","MLM2950827361"]
print("=== Set $549 ===")
for iid in NINE:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    cur=g.get("price")
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":549},timeout=15)
    print(f"  {iid} ${cur}→$549 http={r.status_code}")
    time.sleep(0.3)

# Dedup check de 2950839661
print("\n=== Dedup check MLM2950839661 ===")
g=requests.get(f"{API}/items/MLM2950839661",headers=H,timeout=10).json()
cpid=g.get("catalog_product_id")
print(f"  status={g.get('status')} cpid={cpid} title='{(g.get('title') or '')[:40]}' price=${g.get('price')}")
# Buscar otros active con mismo cpid
ids=[]; off=0
while True:
    r=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []; ids.extend(res)
    if len(res)<50 or off>1000: break
    off+=50
same=[]
for i in range(0,len(ids),20):
    mg=requests.get(f"{API}/items?ids={','.join(ids[i:i+20])}",headers=H,timeout=15).json()
    for e in mg:
        b=e.get("body") or {}
        if b.get("catalog_product_id")==cpid and b.get("id")!="MLM2950839661":
            same.append((b.get("id"),b.get("price"),b.get("sold_quantity",0)))
if same:
    print(f"  ⚠ DUPLICADO! otros con cpid {cpid}: {same}")
else:
    print(f"  ✅ NO duplicada (única con cpid {cpid})")
