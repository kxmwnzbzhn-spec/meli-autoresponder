"""Broader search: filter by name/title containing celeste|aqua even if COLOR attr says different."""
import os, requests, json, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Very broad queries
queries=[
    "JBL Go 4 Celeste","JBL Go 4 Aqua","JBL Go 4 azul claro","JBL Go 4 cyan",
    "JBL Go 4 turquesa","JBL Go 4 mint","JBL Go 4 menta","JBL Go 4 cielo",
    "JBL Go 4 light blue","JBL Go4 Aqua","JBL Go4 Celeste",
    "Bocina JBL Go 4 celeste","Parlante JBL Go 4 celeste",
    "Bocina JBL Go 4 aqua","Parlante JBL Go 4 aqua",
    "JBL Go 4 aquamarino","JBL Go 4 turquoise",
    "JBL Go 4","JBL Go4",  # very broad — filter later
]

# Light-blue family keywords (look in NAME too, not just COLOR)
LB=["celeste","aqua","azul claro","light blue","turquesa","mint","menta","cielo","aquamarino","cyan","cian","turquoise"]

cpids={}
for q in queries:
    rr=requests.get(f"{API}/products/search",headers=H,
        params={"site_id":"MLM","status":"active","q":q,"limit":50},timeout=15)
    if rr.status_code!=200: continue
    for it in (rr.json().get("results") or []):
        cpid=it.get("id")
        if not cpid or not cpid.startswith("MLM"): continue
        cpids[cpid]={"name":it.get("name",""),"first_q":q}

print(f"Total candidate CPIDs from search: {len(cpids)}")

matched=[]
checked=0
for cpid,seed in cpids.items():
    try:
        p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=8).json()
    except: continue
    checked+=1
    name_full=(p.get("name") or "")
    name=name_full.lower()
    # Must be JBL Go 4 product line
    if not ("go 4" in name or "go4" in name.replace(" ","")): continue
    # Exclude cases/funda/Go 3/Pro/Essential
    if any(skip in name for skip in ["go 3","essential","case","funda","protect","cubierta","estuche","octabox","monopatín","scooter"]): continue
    color=""
    for a in (p.get("attributes") or []):
        if a.get("id")=="COLOR":
            color=(a.get("value_name") or ""); break
    cl=color.lower()
    # Match in COLOR or in NAME
    in_color=any(kw in cl for kw in LB)
    in_name=any(kw in name for kw in LB)
    if not (in_color or in_name): continue
    agg=p.get("aggregated_sales") or 0
    if not agg:
        bw=p.get("buy_box_winner") or {}
        agg=bw.get("sold_quantity") or 0
    matched.append({
        "cpid":cpid,
        "name":name_full,
        "color":color,
        "sales":agg,
        "price":(p.get("buy_box_winner") or {}).get("price"),
        "link":p.get("permalink") or f"https://www.mercadolibre.com.mx/p/{cpid}",
        "in_color":in_color,"in_name":in_name,
    })
    time.sleep(0.1)

print(f"Checked: {checked} | Matched (celeste/aqua family by COLOR or NAME): {len(matched)}")
matched.sort(key=lambda x:-(x["sales"] or 0))
print("\n=== RESULTS (sorted by sales desc) ===")
for m in matched:
    src="C+N" if (m["in_color"] and m["in_name"]) else ("C" if m["in_color"] else "N")
    print(f"  [{src}] sales={m['sales']:>5}  {m['cpid']}  | COLOR={m['color']:<25} | {m['name'][:90]}")
    print(f"        {m['link']}")
print("\nJSON:")
print(json.dumps(matched,ensure_ascii=False))
