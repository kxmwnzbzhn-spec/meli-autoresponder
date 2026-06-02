"""Find Alma de Tenochtitlan + Flor de Nopal in ASVA, verify state and priority_replenish."""
import os, requests, json
API="https://api.mercadolibre.com"
SBU=os.environ.get("SUPABASE_URL","").rstrip("/")
SBK=os.environ.get("SUPABASE_SERVICE_KEY","")
SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}"} if SBK else None

r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_ASVA"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ASVA={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me["id"]; print(f"seller={uid}")

# 1) Search Asva items for tenochtitlan + nopal
print("\n=== Searching ASVA active+paused items for Tenochtitlan / Nopal ===")
found=[]
for st in ["active","paused"]:
    off=0
    while off<2000:
        s=requests.get(f"{API}/users/{uid}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        ids=s.get("results") or []
        if not ids: break
        # Multiget
        for i in range(0,len(ids),20):
            batch=",".join(ids[i:i+20])
            mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,status,sub_status,available_quantity,price,inventory_id,catalog_product_id"},timeout=15).json()
            for x in mg:
                if x.get("code")!=200: continue
                b=x["body"]; t=(b.get("title") or "").lower()
                if "tenoch" in t or "nopal" in t or "flor de nopal" in t:
                    found.append(b)
                    print(f"  {b['id']} | status={b.get('status')} sub={b.get('sub_status')} qty={b.get('available_quantity')} inv={b.get('inventory_id')} | {b.get('title')[:75]}")
        if len(ids)<50: break
        off+=50

# 2) Verify priority_replenish has them
if SBH:
    print("\n=== meli_priority_replenish (current rows for ASVA) ===")
    rr=requests.get(f"{SBU}/rest/v1/meli_priority_replenish?account=eq.ASVA&select=*",headers=SBH,timeout=10)
    print(f"HTTP {rr.status_code}: {rr.text[:2000]}")

# 3) Force reactivate found items + ensure in priority list
if SBH and found:
    print("\n=== ADD/UPSERT into priority_replenish + FORCE reactivate ===")
    for b in found:
        iid=b["id"]
        # PUT to force qty=1 active
        rp=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"active","available_quantity":1},timeout=15)
        print(f"  {iid} REACTIVATE → HTTP {rp.status_code}: {rp.text[:200]}")
        # Upsert in priority
        upr={"item_id":iid,"account":"ASVA","default_qty":1,"product_name":b.get("title","")[:200]}
        ru=requests.post(f"{SBU}/rest/v1/meli_priority_replenish",
            headers={**SBH,"Content-Type":"application/json","Prefer":"resolution=merge-duplicates,return=minimal"},
            json=upr,timeout=10)
        print(f"  {iid} PRIORITY upsert → HTTP {ru.status_code}: {ru.text[:200]}")

# 4) Show all priority items after
if SBH:
    print("\n=== priority_replenish AFTER (ASVA) ===")
    rr=requests.get(f"{SBU}/rest/v1/meli_priority_replenish?account=eq.ASVA&select=item_id,default_qty,product_name",headers=SBH,timeout=10)
    print(f"HTTP {rr.status_code}: {rr.text[:2000]}")
