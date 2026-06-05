"""Search MELI catalog products for JBL Go 4 Celeste and Aqua, rank by sales."""
import os, requests, json, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_CLARIBEL={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}

# Try several search queries
queries=[
    "JBL Go 4 Celeste",
    "JBL Go 4 Aqua",
    "JBL Go4 Celeste",
    "JBL Go4 Aqua",
    "jbl go 4 azul claro",
    "jbl go 4 light blue",
]

cpids_seen={}
for q in queries:
    print(f"\n=== Search: '{q}' ===")
    # /products/search is the catalog product search
    for endpoint in [
        ("/products/search", {"site_id":"MLM","status":"active","q":q,"limit":20}),
        ("/sites/MLM/search", {"q":q,"category":"MLM59800","limit":50}),
    ]:
        ep,params=endpoint
        rr=requests.get(f"{API}{ep}",headers=H,params=params,timeout=15)
        if rr.status_code!=200:
            print(f"  {ep} HTTP {rr.status_code}")
            continue
        d=rr.json()
        results=d.get("results") or []
        print(f"  {ep}: {len(results)} results")
        for it in results[:30]:
            cpid=it.get("catalog_product_id") or it.get("id")
            name=it.get("name") or it.get("title","")
            if not cpid: continue
            # Only catalog products start with MLM and are products
            if cpid.startswith("MLM") and ("Go 4" in name or "Go4" in name.replace(" ","")):
                if cpid not in cpids_seen:
                    cpids_seen[cpid]={"name":name,"first_query":q}

print(f"\n=== UNIQUE CPIDs found: {len(cpids_seen)} ===")
for cpid,info in cpids_seen.items():
    print(f"  {cpid}: {info['name'][:80]}")

# For each CPID, get product details + aggregate sales
print(f"\n=== Sales per CPID (sum from all listings) ===")
results=[]
for cpid in list(cpids_seen.keys())[:30]:
    info=cpids_seen[cpid]
    # Get product details
    try:
        p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=10).json()
    except Exception as e:
        print(f"  {cpid} ERR {e}"); continue
    color=None
    for a in (p.get("attributes") or []):
        if a.get("id")=="COLOR":
            color=a.get("value_name"); break
    # Filter Celeste/Aqua/Light blue
    if color and not any(c in color.lower() for c in ["celeste","aqua","azul claro","light blue"]):
        continue
    # Get aggregated listings + sales
    try:
        li=requests.get(f"{API}/products/{cpid}/items?limit=50",headers=H,timeout=15).json()
    except: li={}
    total_sales=0; total_listings=0; active_listings=0; min_price=None
    for r in (li.get("results") or []):
        sold=r.get("sold_quantity") or 0
        total_sales+=sold; total_listings+=1
        if (r.get("status") or "").lower()=="active": active_listings+=1
        pr=r.get("price")
        if pr and (min_price is None or pr<min_price): min_price=pr
    results.append({
        "cpid":cpid,
        "name":p.get("name") or info["name"],
        "color":color,
        "total_sales":total_sales,
        "active_listings":active_listings,
        "total_listings":total_listings,
        "min_price":min_price,
        "permalink":p.get("permalink") or f"https://www.mercadolibre.com.mx/p/{cpid}",
    })
    print(f"  {cpid} | {color} | sales={total_sales} listings={active_listings}/{total_listings} min=${min_price}")
    time.sleep(0.3)

# Sort by sales desc
results.sort(key=lambda x:-(x["total_sales"] or 0))
print(f"\n=== FINAL RANKING ({len(results)} CPIDs) ===")
print(json.dumps(results,ensure_ascii=False,indent=2))
