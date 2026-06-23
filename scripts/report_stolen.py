import os,requests,json,time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Search broad JBL Go 4 catalogs, paginate
queries=["JBL Go 4","JBL GO 4","Bocina JBL Go 4","JBL Go4"]
all_cpids=set()
for q in queries:
  for offset in (0,10,20,30,40):
    url=f"{API}/products/search?q={q.replace(' ','%20')}&site_id=MLM&offset={offset}&limit=10"
    r=requests.get(url,headers=H,timeout=15)
    if r.status_code!=200: break
    res=r.json().get("results",[])
    if not res: break
    for it in res:
      cpid=it.get("id") or it.get("catalog_product_id")
      name=(it.get("name") or "").lower()
      if "go 4" in name or "go4" in name:
        all_cpids.add(cpid)
print(f"Total CPID candidates: {len(all_cpids)}")

# Inspect each, filter only JBL Go 4 (no Go 3, no Charge, etc) and extract color + sold_quantity
results=[]
for cpid in sorted(all_cpids):
  try:
    p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=10).json()
  except: continue
  name=(p.get("name") or "")
  status=p.get("status")
  # Heuristic: must contain "Go 4" or "GO4" but not other models
  if not (("go 4" in name.lower() or "go4" in name.lower()) and "jbl" in name.lower()): continue
  if any(x in name.lower() for x in ["go 3","clip","charge","flip","pulse","tune","reflect","wave","boombox","party","xtreme"]): continue
  if status!="active": continue
  
  color=None
  model=None
  brand=None
  for a in (p.get("attributes") or []):
    if a.get("id") in ("COLOR","MAIN_COLOR") and not color:
      color=a.get("value_name")
    if a.get("id")=="MODEL" and not model:
      model=a.get("value_name")
    if a.get("id")=="BRAND":
      brand=a.get("value_name")
  bbw=p.get("buy_box_winner") or {}
  sold=bbw.get("sold_quantity")
  # try children sum if no sold here
  if not sold:
    # try /products/{cpid}/items
    try:
      its=requests.get(f"{API}/products/{cpid}/items?limit=5",headers=H,timeout=10).json()
      pass
    except: pass
  price_min=p.get("price_from") or bbw.get("price")
  parent=p.get("parent_id")
  ch=len(p.get("children_ids") or [])
  results.append({"cpid":cpid,"name":name,"brand":brand,"color":color,"sold":sold,"price":price_min,"status":status,"parent":parent,"children":ch})

# Sort by sold desc
results.sort(key=lambda x: (x.get("sold") or 0), reverse=True)
print(f"\n=== JBL GO 4 ACTIVE CATALOGS ({len(results)}) ===")
for r in results:
  print(f"  {r['cpid']:20} | color={r.get('color') or '-':16} | sold={r.get('sold') or 0:>6} | ${r.get('price') or '?'} | parent={r.get('parent') or '-'} | kids={r['children']} | {r['name'][:70]}")
