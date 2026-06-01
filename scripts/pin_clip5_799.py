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
CLIP5_SKUS={"ELEC-011","ELEC-012","ELEC-018","ELEC-029","ELEC-031"}
all_ids=[]
for st in ("active","paused"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        all_ids.extend(res)
        if len(res)<50 or off>1000: break
        off+=50

clip5=[]
for i in range(0,len(all_ids),20):
    batch=",".join(all_ids[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,status,price,attributes"},timeout=20).json()
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]
        sku=None
        for a in (b.get("attributes") or []):
            if a.get("id")=="SELLER_SKU": sku=a.get("value_name")
        title=(b.get("title") or "").lower()
        is_clip5=(sku in CLIP5_SKUS) or ("clip 5" in title or "clip5" in title)
        if is_clip5:
            clip5.append((b["id"],b.get("title","")[:55],b.get("status"),b.get("price"),sku))

print(f"\nClip 5 detected: {len(clip5)}")
ok=err=0
for iid,title,st,cur,sku in clip5:
    body={"price":799,"available_quantity":1}
    if st=="paused": body["status"]="active"
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json=body,timeout=20)
    if r.status_code in (200,201):
        ok+=1
        print(f"  {iid} sku={sku} {st} ${cur}->$799: OK")
    else:
        err+=1
        print(f"  {iid} sku={sku} {st} ${cur}->$799: {r.status_code} {r.text[:120]}")
    time.sleep(0.3)
print(f"\n=== DONE ok={ok} err={err} ===")
