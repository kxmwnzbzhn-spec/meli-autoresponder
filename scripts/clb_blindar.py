"""Blindar Claribel:
1) Pull ALL Claribel listings (active+paused)
2) For each Go 4 → set price=$549 + force active+qty=1
3) For each catalog_listing → add to meli_priority_replenish (bot las mantiene active)
4) Reactivar TODAS las pausadas catalog
"""
import os, requests, time, json
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

SB_URL=os.environ.get("SUPABASE_URL","https://wnuhslmryspnypbxbfjf.supabase.co")
SB_KEY=os.environ.get("SUPABASE_SERVICE_KEY","") or os.environ.get("SUPABASE_ANON_KEY","")

# Scan all listings
all_ids=[]
for st in ("active","paused"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        all_ids.extend(res)
        if len(res)<50 or off>1500: break
        off+=50
print(f"Total scanned: {len(all_ids)}")

GO4_SKUS={"ELEC-009","ELEC-010","ELEC-027","ELEC-030"}
catalog_items=[]
go4_items=[]
priority_rows=[]
for i in range(0,len(all_ids),20):
    batch=",".join(all_ids[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,status,sub_status,price,available_quantity,catalog_product_id,catalog_listing,attributes"},timeout=20).json()
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]
        sku=None
        for a in (b.get("attributes") or []):
            if a.get("id")=="SELLER_SKU": sku=a.get("value_name")
        is_catalog=b.get("catalog_listing") is True
        title=(b.get("title") or "")
        is_go4=(sku in GO4_SKUS) or (("go 4" in title.lower() or "go4" in title.lower()) and "go 3" not in title.lower())
        if is_catalog:
            catalog_items.append((b["id"],title[:50],b.get("status"),b.get("sub_status"),b.get("price"),sku,b.get("catalog_product_id")))
            priority_rows.append({"item_id":b["id"],"account":"Claribel","default_qty":1,"product_name":title[:80],"reason":"auto_protected_claribel_catalog"})
        if is_go4:
            go4_items.append((b["id"],title[:50],b.get("status"),b.get("price"),sku))

print(f"\ncatalog_items: {len(catalog_items)}")
print(f"go4_items: {len(go4_items)}")

# A) Go 4 → set $549 + force active
print("\n=== Go 4 to $549 + force active ===")
for iid,title,st,cur,sku in go4_items:
    body={"price":549,"available_quantity":1}
    if st=="paused": body["status"]="active"
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json=body,timeout=20)
    print(f"  {iid} sku={sku} {st} ${cur}->$549 active qty=1: {r.status_code}")
    time.sleep(0.3)

# B) Catalog pausados → reactivar
print("\n=== Catalog paused → active ===")
revived=0
for iid,title,st,ss,cur,sku,cpid in catalog_items:
    if st!="paused": continue
    r=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active","available_quantity":1},timeout=15)
    if r.status_code in (200,201): revived+=1
    print(f"  {iid} sub={ss} -> active: {r.status_code}")
    time.sleep(0.3)
print(f"  revived: {revived}")

# C) Upsert priority_replenish para TODOS los catalog
print(f"\n=== Upsert {len(priority_rows)} rows to meli_priority_replenish ===")
if SB_KEY and priority_rows:
    try:
        r=requests.post(f"{SB_URL}/rest/v1/meli_priority_replenish",
            headers={"apikey":SB_KEY,"Authorization":f"Bearer {SB_KEY}","Content-Type":"application/json","Prefer":"return=minimal,resolution=merge-duplicates"},
            json=priority_rows,timeout=20)
        print(f"  supabase upsert: {r.status_code} {r.text[:200] if r.status_code>=400 else 'OK'}")
    except Exception as e: print(f"  exc: {e}")
else:
    print(f"  ⚠ No SB key (rows={len(priority_rows)}) — output rows for manual insert:")
    print(json.dumps(priority_rows[:30]))
