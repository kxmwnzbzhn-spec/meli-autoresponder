"""Set price=499 a todas las JBL Go 4 en Claribel.
Filtra por SKU (ELEC-009/010/027/030) Y por título que contenga 'Go 4' / 'Go4' (doble safety).
"""
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

# List active + paused (in case user wants to set price even on paused)
all_ids=[]
for st in ("active","paused"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        all_ids.extend(res)
        if len(res)<50 or off>1000: break
        off+=50
print(f"\nClaribel total active+paused: {len(all_ids)}")

go4_items=[]
for i in range(0,len(all_ids),20):
    batch=",".join(all_ids[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,status,price,available_quantity,attributes"},timeout=20).json()
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]
        sku=None
        for a in (b.get("attributes") or []):
            if a.get("id")=="SELLER_SKU": sku=a.get("value_name")
        title=(b.get("title") or "").lower()
        is_go4_sku=sku in GO4_SKUS
        is_go4_title=("go 4" in title or "go4" in title) and "go 3" not in title
        if is_go4_sku or is_go4_title:
            go4_items.append((b["id"],b.get("title","")[:60],b.get("status"),b.get("price"),sku))

print(f"\nJBL Go 4 detectados: {len(go4_items)}")
ok=0; err=0; nochange=0
for iid,title,st,cur,sku in go4_items:
    if cur==499:
        nochange+=1
        print(f"  {iid} {st} sku={sku} ${cur} (already $499) | {title}")
        continue
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"price":499},timeout=20)
    if r.status_code in (200,201):
        ok+=1
        print(f"  {iid} {st} sku={sku} ${cur}->$499 OK | {title}")
    else:
        err+=1
        print(f"  {iid} {st} sku={sku} ${cur} ERR {r.status_code} {r.text[:120]} | {title}")
    time.sleep(0.3)

print(f"\n=== DONE === changed_to_499={ok} already_499={nochange} err={err}")
