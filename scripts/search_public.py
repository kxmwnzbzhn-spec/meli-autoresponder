"""Try site search without bearer to find listings with 'celeste'/'aqua' in title -> CPIDs."""
import os, requests, json
API="https://api.mercadolibre.com"

queries=["JBL Go 4 Celeste","JBL Go 4 Aqua","JBL Go4 Aqua","JBL Go4 Celeste",
         "Bocina JBL Go 4 Aqua","Parlante JBL Go 4 Aqua",
         "bocina go 4 celeste","bocina go 4 aqua"]

# Try without auth
cpids={}
for q in queries:
    for headers in [{},{"User-Agent":"Mozilla/5.0"}]:
        rr=requests.get(f"{API}/sites/MLM/search",
            params={"q":q,"category":"MLM59800","limit":50},headers=headers,timeout=15)
        print(f"  q='{q}' no-auth headers={list(headers.keys())} HTTP {rr.status_code}")
        if rr.status_code==200:
            res=rr.json().get("results") or []
            print(f"    {len(res)} results")
            for r in res[:25]:
                cpid=r.get("catalog_product_id")
                title=r.get("title","")
                if cpid and ("go 4" in title.lower() or "go4" in title.lower().replace(" ","")):
                    cpids.setdefault(cpid,[]).append(title[:90])
            break

print(f"\n=== Unique CPIDs from public search: {len(cpids)} ===")
for cpid,titles in cpids.items():
    print(f"  {cpid}: {titles[0]}")
