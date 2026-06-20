import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPIDS=["MLM70245995","MLM70063831","MLM70063753","MLM70063777","MLM70063872","MLM69794803"]
results=[]
for CPID in CPIDS:
  print(f"\n=== {CPID} ===")
  cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
  name=cp.get("name","")
  print(f"  name: {name[:80]}")
  print(f"  domain: {cp.get('domain_id')} pdp: {cp.get('pdp_types')}")
  
  # Find category
  cat="MLM1271"  # perfumes default since pattern Alchemia Lab
  i=requests.get(f"{API}/products/{CPID}/items?limit=3",headers=H,timeout=15).json()
  for r2 in (i.get("results") or []):
    iid=r2.get("item_id")
    if iid:
      try:
        ci=requests.get(f"{API}/items/{iid}?attributes=category_id",headers=H,timeout=10).json()
        if ci.get("category_id"): cat=ci["category_id"]; break
      except: pass
  ps=[r2.get("price") for r2 in (i.get("results") or []) if r2.get("price")]
  ps.sort()
  if ps: print(f"  competidores: {len(ps)} min={ps[0]}")
  else: print("  sin competidores")
  
  TITLE=name[:60] if len(name)<=60 else " ".join(name.split()[:9])[:60]
  
  payload={
    "title": TITLE,
    "catalog_product_id": CPID,
    "catalog_listing": True,
    "category_id": cat,
    "price": 399,
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
    results.append((CPID,d.get("id"),d.get("title"),d.get("permalink")))
    print(f"  ✅ {d.get('id')} @ ${d.get('price')}")
  else:
    print(f"  ❌ {p.text[:500]}")

print("\n=== SUMMARY ===")
for c,i,t,u in results:
  print(f"  {c} → {i} @ $399")
  print(f"    {t[:70]}")
  print(f"    {u}")
