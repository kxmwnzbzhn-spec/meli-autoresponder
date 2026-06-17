import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

results=[]
for CPID in ["MLM42426004","MLM45472872"]:
  print(f"\n=== {CPID} ===")
  cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
  print(f"  name: {cp.get('name','?')[:80]}")
  print(f"  domain: {cp.get('domain_id')} pdp: {cp.get('pdp_types')}")
  # find category from existing items
  i=requests.get(f"{API}/products/{CPID}/items?limit=5",headers=H,timeout=15).json()
  cat=None
  for r2 in i.get("results",[]):
    iid=r2.get("item_id")
    if iid:
      g=requests.get(f"{API}/items/{iid}?attributes=category_id",headers=H,timeout=10).json()
      cat=g.get("category_id")
      if cat: break
  print(f"  category: {cat}")
  
  # Existing competition
  ps=[]
  for r2 in (i.get("results") or [])[:10]:
    p=r2.get("price")
    if p: ps.append(p)
  ps.sort()
  if ps:
    print(f"  competidores: {len(ps)} | min={ps[0]} median={ps[len(ps)//2]} max={ps[-1]}")
  
  payload={
    "catalog_product_id":CPID,
    "catalog_listing":True,
    "category_id":cat or "MLM59800",
    "price":1999,
    "currency_id":"MXN",
    "available_quantity":1,
    "listing_type_id":"gold_pro",
    "condition":"new",
    "buying_mode":"buy_it_now",
    "sale_terms":[
      {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
      {"id":"WARRANTY_TIME","value_name":"30 días"}
    ]
  }
  p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
  print(f"  POST: {p.status_code}")
  if p.status_code==201:
    d=p.json()
    iid=d.get("id")
    results.append((CPID,iid,d.get("title")))
    print(f"  ✅ CREATED {iid} @ ${d.get('price')} status={d.get('status')}")
    print(f"  permalink: {d.get('permalink')}")
  else:
    print(f"  ERROR: {p.text[:600]}")

print("\n=== SUMMARY ===")
for c,i,t in results:
  print(f"  {c} → {i} | {t[:60]}")
