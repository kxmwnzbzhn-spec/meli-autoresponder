import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]

GO4_SKUS={"ELEC-009","ELEC-010","ELEC-027","ELEC-030"}

all_ids=[]
for st in ("active","paused"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        all_ids.extend(res)
        if len(res)<50 or off>1000: break
        off+=50

go4_items=[]
for i in range(0,len(all_ids),20):
    batch=",".join(all_ids[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,status,price,catalog_product_id,attributes"},timeout=20).json()
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]
        sku=None
        for a in (b.get("attributes") or []):
            if a.get("id")=="SELLER_SKU": sku=a.get("value_name")
        title=(b.get("title") or "").lower()
        is_go4=(sku in GO4_SKUS) or (("go 4" in title or "go4" in title) and "go 3" not in title)
        if is_go4:
            go4_items.append((b["id"],b.get("title","")[:55],b.get("status"),b.get("price"),sku,b.get("catalog_product_id")))

print(f"\nJBL Go 4 detectados: {len(go4_items)}")
cpids_to_pin=set()
for iid,title,st,cur,sku,cpid in go4_items:
    if cpid: cpids_to_pin.add(cpid)
    if cur==599:
        print(f"  {iid} sku={sku} ${cur} (already $599)")
        continue
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":599},timeout=20)
    print(f"  {iid} sku={sku} ${cur}->$599: {r.status_code} {r.text[:80] if r.status_code>=400 else 'OK'}")
    time.sleep(0.3)

print(f"\nCPIDs to PIN at 599 in Supabase strategy: {len(cpids_to_pin)}")
print(",".join(sorted(cpids_to_pin)))
