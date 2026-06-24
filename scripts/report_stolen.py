import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_MAYRELY"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

results={}
for cpid in ["MLM25912333","MLM41991186"]:
  cp=requests.get(f"{API}/products/{cpid}",headers=HJ,timeout=15).json()
  print(f"\n=== {cpid}: {cp.get('name')} status={cp.get('status')} ===")
  it=requests.get(f"{API}/products/{cpid}/items?limit=5",headers=HJ,timeout=10).json()
  cats=[i.get("category_id") for i in it.get("results",[])[:3]]
  cat=cats[0] if cats else "MLM59800"
  print(f"  cat: {cat}")
  title=cp.get("name","")[:60]
  payload={
    "catalog_listing": True,
    "catalog_product_id": cpid,
    "category_id": cat,
    "price": 799,
    "currency_id": "MXN",
    "available_quantity": 1,
    "listing_type_id": "gold_pro",
    "condition": "new",
    "title": title,
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}]
  }
  r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
  j={}
  try: j=r.json()
  except: pass
  iid=j.get("id")
  print(f"  PUBLISH {r.status_code} -> {iid}")
  if r.status_code>=400:
    print(f"  ERR: {r.text[:600]}")
  results[cpid]={"item":iid,"status":r.status_code}

print("\nRESULTS:",json.dumps(results,indent=2))
