"""Broader search: JBL Go 4 with light-blue family colors + aggregated_sales from product."""
import os, requests, json, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}

queries=[
    "JBL Go 4 Celeste",
    "JBL Go 4 Aqua",
    "JBL Go4 Celeste",
    "JBL Go4 Aqua",
    "JBL Go 4 azul claro",
    "JBL Go 4 turquesa",
    "JBL Go 4 menta",
    "JBL Go 4 mint",
    "JBL Go 4 light blue",
    "JBL Go 4",  # broad — filter later
]

# Light-blue color family keywords
LB_COLORS=["celeste","aqua","azul claro","light blue","turquesa","mint","menta","aquamarino","cielo"]

cpids={}
for q in queries:
    params={"site_id":"MLM","status":"active","q":q,"limit":50}
    rr=requests.get(f"{API}/products/search",headers=H,params=params,timeout=15)
    if rr.status_code!=200: continue
    for it in (rr.json().get("results") or []):
        cpid=it.get("id") or it.get("catalog_product_id")
        if not cpid or not cpid.startswith("MLM"): continue
        cpids[cpid]=True

print(f"Total candidate CPIDs: {len(cpids)}")

# Filter: GET product details, check color and that it's JBL Go 4
matched=[]
for cpid in cpids:
    try:
        p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=10).json()
    except: continue
    name=(p.get("name") or "").lower()
    family=(p.get("family_name") or "").lower()
    # Must be JBL Go 4 (not Go 3, Go Essential, Pro, Plus, etc.)
    is_go4 = ("go 4" in name or "go4" in name.replace(" ","")) and "go 3" not in name and "essential" not in name and "pro" not in name and "plus" not in name
    if not is_go4: continue
    color=None
    for a in (p.get("attributes") or []):
        if a.get("id")=="COLOR":
            color=(a.get("value_name") or "")
            break
    if not color: continue
    cl=color.lower()
    if not any(kw in cl for kw in LB_COLORS): continue
    # Aggregated sales
    agg=p.get("aggregated_sales") or 0
    if not agg:
        # Try buy_box_winner.sold_quantity
        bw=p.get("buy_box_winner") or {}
        agg=bw.get("sold_quantity") or 0
    matched.append({
        "cpid":cpid,
        "name":p.get("name"),
        "color":color,
        "aggregated_sales":agg,
        "buy_box_price":(p.get("buy_box_winner") or {}).get("price"),
        "permalink":p.get("permalink") or f"https://www.mercadolibre.com.mx/p/{cpid}",
    })
    time.sleep(0.2)

# Sort by aggregated_sales desc
matched.sort(key=lambda x: -(x["aggregated_sales"] or 0))

print(f"\n=== JBL Go 4 Celeste/Aqua family — {len(matched)} CPIDs ===")
for m in matched:
    print(f"  sales={m['aggregated_sales']:>5}  {m['cpid']}  | {m['color']:<25} | ${m['buy_box_price']} | {m['name'][:70]}")
    print(f"    {m['permalink']}")

print(json.dumps(matched,ensure_ascii=False,indent=2))
