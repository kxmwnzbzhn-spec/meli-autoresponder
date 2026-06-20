import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# YC token (para probar acceso al MLM5374101788)
RT_Y=os.environ.get("MELI_REFRESH_TOKEN_YC_NEW")
AT_Y=None
if RT_Y:
  ry=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_Y},timeout=20)
  if ry.status_code<400: AT_Y=ry.json()["access_token"]

def publish_catalog(cpid, price, category=None):
  print(f"\n=== {cpid} → catalog $${price} ===")
  cp=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
  name=cp.get("name","")
  print(f"  name: {name[:80]}")
  # Find category
  cat=category
  if not cat:
    i=requests.get(f"{API}/products/{cpid}/items?limit=3",headers=H,timeout=15).json()
    for r2 in (i.get("results") or []):
      iid=r2.get("item_id")
      if iid:
        try:
          ci=requests.get(f"{API}/items/{iid}?attributes=category_id",headers=H,timeout=10).json()
          if ci.get("category_id"): cat=ci["category_id"]; break
        except: pass
    if not cat: cat="MLM59800"
  # Snapshot
  i=requests.get(f"{API}/products/{cpid}/items?limit=10",headers=H,timeout=15).json()
  ps=[r2.get("price") for r2 in (i.get("results") or []) if r2.get("price")]
  ps.sort()
  if ps: print(f"  competidores: {len(ps)} min={ps[0]} median={ps[len(ps)//2]}")
  TITLE=name[:60]
  payload={
    "title":TITLE,"catalog_product_id":cpid,"catalog_listing":True,"category_id":cat,
    "price":price,"currency_id":"MXN","available_quantity":1,"listing_type_id":"gold_pro",
    "condition":"new","buying_mode":"buy_it_now",
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}]
  }
  p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
  print(f"  POST: {p.status_code}")
  if p.status_code==201:
    d=p.json()
    print(f"  ✅ {d.get('id')} @ ${d.get('price')} status={d.get('status')}")
    print(f"  permalink: {d.get('permalink')}")
    return d.get("id")
  else:
    print(f"  ❌ {p.text[:400]}")
    return None

# A) MLM2950839631 → CPID MLM50131488 Bose SoundLink Home @ $1999
publish_catalog("MLM50131488", 1999, category=None)

# B) MLM5374101788 — probe first
print("\n=== PROBE MLM5374101788 ===")
hit=None
for name,tok in [("AH",AT),("YC_NEW",AT_Y)]:
  if not tok: continue
  g=requests.get(f"{API}/items/MLM5374101788?attributes=id,title,price,status,seller_id,catalog_product_id,category_id",
                 headers={"Authorization":f"Bearer {tok}"},timeout=15)
  if g.status_code==200:
    info=g.json()
    print(f"  via {name}: {info}")
    hit=info
    break
  else:
    print(f"  {name} HTTP {g.status_code}")

if hit:
  CPID=hit.get("catalog_product_id")
  CAT=hit.get("category_id")
  if CPID:
    publish_catalog(CPID, 199, category=CAT)
  else:
    print("  → no CPID, would need clone (not implemented in batch)")
