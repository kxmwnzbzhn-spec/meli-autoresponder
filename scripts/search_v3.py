"""Dump ALL JBL Go 4 CPIDs with color + aggregated_sales, let user filter."""
import os, requests, json, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}

queries=["JBL Go 4","JBL Go4","Jbl Go 4","Bocina JBL Go 4","Parlante JBL Go 4"]
cpids={}
for q in queries:
    rr=requests.get(f"{API}/products/search",headers=H,
        params={"site_id":"MLM","status":"active","q":q,"limit":50},timeout=15)
    if rr.status_code!=200: continue
    for it in (rr.json().get("results") or []):
        cpid=it.get("id")
        if cpid and cpid.startswith("MLM"): cpids[cpid]=True

print(f"Total candidate CPIDs: {len(cpids)}")
LB=["celeste","aqua","azul claro","light blue","turquesa","mint","menta","cielo","aquamarino","cyan","cian"]

matched=[]
for cpid in cpids:
    try:
        p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=10).json()
    except: continue
    name=(p.get("name") or "").lower()
    if not ("go 4" in name or "go4" in name.replace(" ","")): continue
    if "go 3" in name or "essential" in name or "case" in name or "funda" in name or "protect" in name: continue
    color=""
    for a in (p.get("attributes") or []):
        if a.get("id")=="COLOR":
            color=a.get("value_name") or ""; break
    agg=p.get("aggregated_sales") or 0
    if not agg:
        bw=p.get("buy_box_winner") or {}
        agg=bw.get("sold_quantity") or 0
    matched.append({
        "cpid":cpid,
        "name":p.get("name"),
        "color":color,
        "sales":agg,
        "price":(p.get("buy_box_winner") or {}).get("price"),
        "link":p.get("permalink") or f"https://www.mercadolibre.com.mx/p/{cpid}",
        "is_lightblue":any(kw in color.lower() for kw in LB),
    })
    time.sleep(0.15)

# Sort: light blue first (sales desc), then rest
matched.sort(key=lambda x: (-int(x["is_lightblue"]), -(x["sales"] or 0)))

print(f"\n=== ALL JBL Go 4 catalog products ({len(matched)}) ===")
print("MARK | SALES | CPID         | COLOR                      | PRICE   | NAME")
for m in matched:
    mark = "★" if m["is_lightblue"] else " "
    print(f"  {mark}  | {m['sales']:>5} | {m['cpid']:<13}| {m['color'][:25]:<25} | ${m['price']!s:<7}| {m['name'][:60]}")

# Filter to light blue family only
lb_only=[m for m in matched if m["is_lightblue"]]
print(f"\n=== CELESTE / AQUA family ({len(lb_only)}) sorted by sales ===")
for m in lb_only:
    print(f"  sales={m['sales']:>5}  {m['cpid']}  | {m['color']:<25} | ${m['price']} | {m['name'][:70]}")
    print(f"    {m['link']}")
print("\nJSON_LB:")
print(json.dumps(lb_only,ensure_ascii=False))
