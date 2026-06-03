"""Audit Adrián paused/OOS items, force reactivate the ones that should be (qty 1+)."""
import os, requests, json, time
API="https://api.mercadolibre.com"
SBU=os.environ.get("SUPABASE_URL","").rstrip("/")
SBK=os.environ.get("SUPABASE_SERVICE_KEY","")
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}"} if SBK else None

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]; print(f"seller={uid}")

# Read locks from Supabase
locked=set()
cpid_bl=set()
if SBH:
    for r in (requests.get(f"{SBU}/rest/v1/meli_no_replenish_items?select=item_id",headers=SBH,timeout=10).json() or []):
        locked.add(r["item_id"])
    for r in (requests.get(f"{SBU}/rest/v1/meli_catalog_blacklist?select=catalog_product_id",headers=SBH,timeout=10).json() or []):
        cpid_bl.add(r["catalog_product_id"])
print(f"locked_items={len(locked)} cpid_blacklist={len(cpid_bl)}")

# All paused
ids=[]; off=0
while off<3000:
    s=requests.get(f"{API}/users/{uid}/items/search?status=paused&limit=50&offset={off}",headers=H,timeout=15).json()
    res=s.get("results") or []
    ids.extend(res)
    if len(res)<50: break
    off+=50
print(f"paused={len(ids)}")

revived=0; skipped_locked=0; skipped_fbm=0; errors=0; not_oos=0
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    try:
        mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,sub_status,catalog_product_id,inventory_id,available_quantity,title"},timeout=15).json()
    except: continue
    for x in mg:
        if x.get("code")!=200: continue
        b=x["body"]; sid=b["id"]
        if "out_of_stock" not in (b.get("sub_status") or []):
            not_oos+=1; continue
        if sid in locked: skipped_locked+=1; continue
        cpid=b.get("catalog_product_id")
        if cpid and cpid in cpid_bl: continue
        if b.get("inventory_id"): skipped_fbm+=1; continue
        try:
            r2=requests.put(f"{API}/items/{sid}",headers=HJ,json={"status":"active","available_quantity":1},timeout=12)
            if r2.status_code in (200,201):
                revived+=1
                print(f"  ✅ {sid} | {(b.get('title') or '')[:60]}")
            else:
                errors+=1
                print(f"  ❌ {sid} HTTP {r2.status_code}: {r2.text[:160]}")
        except Exception as e:
            errors+=1; print(f"  ❌ {sid} EXC {e}")
    time.sleep(0.5)

print(f"\n=== SUMMARY ===")
print(f"  paused total: {len(ids)}")
print(f"  not_oos (no need): {not_oos}")
print(f"  skipped locked: {skipped_locked}")
print(f"  skipped FBM: {skipped_fbm}")
print(f"  ✅ revived: {revived}")
print(f"  ❌ errors: {errors}")
