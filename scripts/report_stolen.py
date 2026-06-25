import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Get all Mayrely items, all statuses
SID=3419500448
items=[]
for status in ("active","paused","under_review","closed"):
  off=0
  while True:
    r=requests.get(f"{API}/users/{SID}/items/search?status={status}&offset={off}&limit=50",headers=H,timeout=15).json()
    res=r.get("results",[])
    if not res: break
    for iid in res: items.append({"iid":iid,"status":status})
    if len(res)<50: break
    off+=50
print(f"TOTAL items: {len(items)}")

# Supabase bounds
SB="https://wnuhslmryspnypbxbfjf.supabase.co"
SBH={"apikey":os.environ["SUPABASE_SERVICE_KEY"],"Authorization":f"Bearer {os.environ['SUPABASE_SERVICE_KEY']}"}
strats={s["catalog_product_id"]:(float(s["floor"] or 0),float(s["ceiling"] or 0)) for s in requests.get(f"{SB}/rest/v1/meli_catalog_strategy?active=eq.true&select=catalog_product_id,floor,ceiling",headers=SBH,timeout=15).json()}
pri={r["item_id"]:r["default_qty"] for r in requests.get(f"{SB}/rest/v1/meli_priority_replenish?account=eq.MAYRELY&select=item_id,default_qty",headers=SBH,timeout=15).json()}

# Enrich each
rows=[]
for entry in items:
  iid=entry["iid"]
  try:
    it=requests.get(f"{API}/items/{iid}?attributes=id,title,price,available_quantity,status,sub_status,catalog_product_id,catalog_listing,listing_type_id",headers=H,timeout=10).json()
  except: continue
  cpid=it.get("catalog_product_id")
  price=it.get("price")
  fl,ce = strats.get(cpid,(None,None))
  in_bounds = None
  if fl and ce and price:
    in_bounds = fl <= price <= ce
  rows.append({
    "iid":iid,"title":(it.get("title") or "")[:55],
    "status":it.get("status"),"sub":",".join(it.get("sub_status") or []),
    "cpid":cpid,"cat":"Si" if it.get("catalog_listing") else "No","listing":it.get("listing_type_id"),
    "price":price,"qty":it.get("available_quantity"),
    "floor":fl,"ceiling":ce,"in_bounds":in_bounds,
    "autostock":"Si" if iid in pri else "No"
  })

# Print summary
print(f"\n{'iid':17}{'cat':4}{'status':14}{'qty':5}{'price':9}{'floor':8}{'ceil':8}{'bounds':8}{'autoq':6}{'title'}")
ok=warn=err=0
for r in rows:
  flag="✓"
  if r["status"]!="active": flag="P" if r["status"]=="paused" else "?"
  if r["price"] and r["floor"]:
    if not r["in_bounds"]: flag="⚠"
  if (r["qty"] or 0)==0 and r["status"]=="active": flag="0stk"
  print(f" {r['iid']:16} {r['cat']:3} {r['status']:13} {r['qty'] or 0:>4} ${r['price'] or 0:>6} ${r['floor'] or 0:>6} ${r['ceiling'] or 0:>6}  {('✓' if r['in_bounds'] else '⚠' if r['floor'] else '-'):>4}  {r['autostock']:>4}  {flag} {r['title']}")
  if flag=="⚠": warn+=1
  elif flag in ("?","0stk"): err+=1
  else: ok+=1
print(f"\nSUMMARY: ok={ok} warn={warn} err={err}")
