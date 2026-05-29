"""Activa 5 listings Claribel a $499, hace audit completo del catálogo activo."""
import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=15).json()
UID=me["id"]

TARGETS=["MLM2967317613","MLM2967317609","MLM2967317601","MLM2967292003","MLM2967292013"]

print("\n=== STEP 1: Activate 5 at $499 ===")
for sid in TARGETS:
    g=requests.get(f"{API}/items/{sid}",headers=H,timeout=15).json()
    sku=None
    for a in (g.get("attributes") or []):
        if a.get("id")=="SELLER_SKU": sku=a.get("value_name")
    st=g.get("status"); cur=g.get("price"); qty=g.get("available_quantity",0)
    print(f"\n{sid} sku={sku} BEFORE: status={st} price=${cur} qty={qty}")
    body={"price":499,"available_quantity":1,"status":"active"}
    r=requests.put(f"{API}/items/{sid}",headers=HJ,json=body,timeout=20)
    print(f"  PUT: {r.status_code} {r.text[:200] if r.status_code>=400 else 'OK'}")
    g2=requests.get(f"{API}/items/{sid}",headers=H,timeout=15).json()
    print(f"  AFTER: status={g2.get('status')} price=${g2.get('price')} qty={g2.get('available_quantity')}")
    time.sleep(0.4)

print("\n\n=== STEP 2: Audit Claribel completo ===")
all_ids=[]; off=0
while True:
    r=requests.get(f"{API}/users/{UID}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
    res=r.get("results") or []
    all_ids.extend(res)
    if len(res)<50 or off>1500: break
    off+=50
also=[]
for st in ("paused","under_review"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        also.extend(res)
        if len(res)<50 or off>1500: break
        off+=50

rows=[]
for batch_ids in [all_ids[i:i+20] for i in range(0,len(all_ids),20)] + [also[i:i+20] for i in range(0,len(also),20)]:
    if not batch_ids: continue
    batch=",".join(batch_ids)
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,status,sub_status,price,available_quantity,sold_quantity,catalog_product_id,attributes"},timeout=20).json()
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]
        sku=None
        for a in (b.get("attributes") or []):
            if a.get("id")=="SELLER_SKU": sku=a.get("value_name")
        rows.append((b["id"],b.get("title","")[:35],b.get("status"),b.get("sub_status") or [],b.get("price"),b.get("available_quantity"),b.get("sold_quantity"),sku,b.get("catalog_product_id")))

actives=[r for r in rows if r[2]=="active"]
paused_oos=[r for r in rows if r[2]=="paused" and "out_of_stock" in r[3]]
paused_other=[r for r in rows if r[2]=="paused" and "out_of_stock" not in r[3]]

print(f"\nTotal Claribel scanned: {len(rows)}")
print(f"  active: {len(actives)}")
print(f"  paused/out_of_stock (needs auto-replenish): {len(paused_oos)}")
print(f"  paused/other: {len(paused_other)}")

print(f"\n--- ACTIVE ({len(actives)}) ---")
for iid,title,st,ss,pr,qty,sold,sku,cpid in actives:
    print(f"  {iid} sku={sku!s:<12} ${pr:<6} qty={qty} sold={sold} | {title}")

print(f"\n--- PAUSED out_of_stock ({len(paused_oos)}) — bot 30s debería reactivarlas ---")
for iid,title,st,ss,pr,qty,sold,sku,cpid in paused_oos:
    print(f"  {iid} sku={sku!s:<12} ${pr:<6} sold={sold} | {title}")

print(f"\n--- PAUSED otros motivos ({len(paused_other)}) — NO reactivar auto ---")
for iid,title,st,ss,pr,qty,sold,sku,cpid in paused_other:
    print(f"  {iid} sku={sku!s:<12} ${pr:<6} sub={ss} sold={sold} | {title}")
