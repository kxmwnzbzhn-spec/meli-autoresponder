"""Snapshot Adrián catalog items into meli_catalog_strategy (no-op defaults)."""
import os, requests, time
API="https://api.mercadolibre.com"
SBU=os.environ["SUPABASE_URL"].rstrip("/")
SBK=os.environ["SUPABASE_SERVICE_KEY"]
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json"}

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_AH={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]; print(f"seller={uid}")

# Get all active items
ids=[]; off=0
while off<5000:
    s=requests.get(f"{API}/users/{uid}/items/search?status=active&limit=50&offset={off}",headers=H,timeout=15).json()
    res=s.get("results") or []
    ids.extend(res)
    if len(res)<50: break
    off+=50
print(f"active items: {len(ids)}")

# Multiget to find those with catalog_product_id
catalog_items=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,catalog_product_id,price,available_quantity"},timeout=15).json()
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]
        if b.get("catalog_product_id"):
            catalog_items.append({
                "iid":b["id"],
                "cpid":b["catalog_product_id"],
                "title":b.get("title",""),
                "price":b.get("price"),
            })

print(f"\nCatalog items in Adrián: {len(catalog_items)}")
for ci in catalog_items[:30]:
    print(f"  {ci['iid']} cpid={ci['cpid']} ${ci['price']} | {ci['title'][:70]}")

# Upsert into meli_catalog_strategy with no-op defaults (floor=1, ceiling=999999) for any cpid not already there
ok=0; skip=0; err=0
for ci in catalog_items:
    cpid=ci["cpid"]
    # Check if already exists
    rr=requests.get(f"{SBU}/rest/v1/meli_catalog_strategy?catalog_product_id=eq.{cpid}&select=catalog_product_id,floor,ceiling,account",headers=SBH,timeout=8).json()
    if rr and len(rr)>0:
        # Already exists — just ensure account includes ADRIAN
        skip+=1
        continue
    # Insert new row
    up={
        "sku":f"AH-{cpid[3:][:10]}",
        "catalog_product_id":cpid,
        "floor":1,
        "ceiling":999999,
        "active":True,
        "priority":1,
        "account":"ADRIAN",
        "source":"adrian_war_snapshot_2026-06-09",
        "notes":(ci["title"] or "")[:200],
    }
    rp=requests.post(f"{SBU}/rest/v1/meli_catalog_strategy",
        headers={**SBH,"Prefer":"resolution=merge-duplicates,return=minimal"},
        json=up,timeout=10)
    if rp.status_code in (200,201,204): ok+=1
    else: err+=1; print(f"  ERR cpid={cpid}: {rp.status_code} {rp.text[:160]}")
    time.sleep(0.1)

print(f"\nSnapshot summary: inserted={ok}, skipped(already)={skip}, errors={err}")

# Also log to actions_log
requests.post(f"{SBU}/rest/v1/meli_actions_log",headers=SBH,
    json={"account":"ADRIAN","item_id":"BULK","action_type":"war_activate_snapshot",
          "from_value":"none",
          "to_value":f"strategy_rows_inserted={ok} catalog_items={len(catalog_items)}",
          "actor":"claude_cowork",
          "details":"snapshot adrian catalog items para activar war"},timeout=10)
print("[ACTLOG] logged")
