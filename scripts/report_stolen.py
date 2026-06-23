import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Color groups
COLORS={
  "Negro":["negro","negra","black"],
  "Celeste":["celeste","cielo","sky"],
  "Rosa":["rosa","pink"],
  "Camuflaje":["camufla","camo","verde camufl","camufl"],
}

# Step 1: gather all JBL Go 4 CPIDs (exhaustive search)
queries=["JBL Go 4","JBL GO 4","Bocina JBL Go 4","Parlante JBL Go 4","Altavoz JBL Go 4","JBL Go4"]
all_cpids={}
for q in queries:
  for offset in (0,10,20,30,40,50):
    url=f"{API}/products/search?q={q.replace(' ','%20')}&site_id=MLM&offset={offset}&limit=10&status=active"
    try: r=requests.get(url,headers=H,timeout=15)
    except: break
    if r.status_code!=200: break
    res=r.json().get("results",[])
    if not res: break
    for it in res:
      cpid=it.get("id") or it.get("catalog_product_id")
      name=(it.get("name") or "").lower()
      if not ("go 4" in name or "go4" in name): continue
      if any(x in name for x in ["go 3","clip","charge","flip","pulse","tune","reflect","wave","boombox","party","xtreme","case","funda","estuche","protect","silicona","cover"]): continue
      if cpid not in all_cpids:
        all_cpids[cpid]={"name":it.get("name"),"domain":it.get("domain_id")}

print(f"Total candidate CPIDs: {len(all_cpids)}")

# Step 2: enrich each CPID with color + sold_quantity
RESULTS=[]
for cpid,meta in all_cpids.items():
  p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=10).json()
  if p.get("status")!="active": continue
  
  # Get color from attributes
  color=None; brand=None
  for a in (p.get("attributes") or []):
    if a.get("id") in ("COLOR","MAIN_COLOR") and not color:
      color=a.get("value_name")
    if a.get("id")=="BRAND" and not brand:
      brand=a.get("value_name")
  # filter only JBL brand
  if brand and brand.upper()!="JBL": continue
  
  # Classify color into our target colors
  cl=(color or meta["name"] or "").lower()
  target=None
  for tk,kws in COLORS.items():
    if any(k in cl for k in kws):
      target=tk; break
  if not target: continue  # skip colors we don't care about

  # Get all items under this CPID, fetch sold_quantity via /items?ids=
  items_data=requests.get(f"{API}/products/{cpid}/items?limit=50",headers=H,timeout=12).json()
  items=items_data.get("results",[])
  total_sold=0; active_items=0
  # batch fetch sold_quantity
  ids=[i.get("item_id") for i in items if i.get("item_id")]
  for chunk_start in range(0,len(ids),20):
    chunk=ids[chunk_start:chunk_start+20]
    ids_str=",".join(chunk)
    bulk=requests.get(f"{API}/items?ids={ids_str}&attributes=id,sold_quantity,status",headers=H,timeout=15)
    if bulk.status_code!=200: continue
    for entry in bulk.json():
      if entry.get("code")==200:
        b=entry.get("body",{})
        sq=b.get("sold_quantity",0) or 0
        if b.get("status")=="active":
          active_items+=1
        total_sold+=sq
  
  bbw=p.get("buy_box_winner") or {}
  price=bbw.get("price")
  RESULTS.append({
    "cpid":cpid,"color":color,"target_color":target,
    "name":meta["name"],"sold":total_sold,"items":len(ids),"active_items":active_items,
    "price":price,
    "permalink":f"https://articulo.mercadolibre.com.mx/{cpid.replace('MLM','MLM-')}"
  })

RESULTS.sort(key=lambda x:(x["target_color"],-x["sold"]))
print(f"\n=== RANKING JBL GO 4 BY TARGET COLOR ({len(RESULTS)}) ===")
for r in RESULTS:
  print(f"  [{r['target_color']:9}] {r['cpid']:14} | {r['color']:25} | ventas={r['sold']:>5} | items={r['items']:>2} (act={r['active_items']}) | ${r['price'] or '?':>6} | {r['name'][:55]}")
print()
print(f"TOP 5 PER COLOR:")
for tk in ["Negro","Celeste","Rosa","Camuflaje"]:
  print(f"\n--- {tk} ---")
  top=sorted([r for r in RESULTS if r["target_color"]==tk],key=lambda x:-x["sold"])[:5]
  for r in top:
    print(f"  {r['cpid']:14} | ventas={r['sold']:>5} | ${r['price'] or '?'} | {r['name'][:60]}")

import json as J
J.dump(RESULTS,open('/tmp/go4_ranking.json','w'),indent=2,default=str)
print("\nDONE")
