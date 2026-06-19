import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# 1) Search for the CPID by title
q="Armaf Club De Nuit Iconic 105ml"
print(f"searching: {q}")
s=requests.get(f"{API}/sites/MLM/search?q={requests.utils.quote(q)}&limit=15",headers=H,timeout=15).json()
cpid=None
cpid_options={}
for r2 in s.get("results",[])[:15]:
  c=r2.get("catalog_product_id")
  if c:
    cpid_options[c]=cpid_options.get(c,0)+1
    print(f"  candidate CPID={c} title={r2.get('title','')[:70]} price={r2.get('price')}")
# Pick most common CPID
if cpid_options:
  cpid=max(cpid_options.items(),key=lambda x:x[1])[0]
print(f"\nselected CPID: {cpid}")

# Also probe via user_product
upr=requests.get(f"{API}/user-products/MLMU3423667933",headers=H,timeout=15)
print(f"user-product: {upr.status_code}")
print(upr.text[:600])

if not cpid:
  raise SystemExit("no CPID found")

cp=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
print(f"\nCPID name: {cp.get('name')}")
i=requests.get(f"{API}/products/{cpid}/items?limit=15",headers=H,timeout=15).json()
ps=[r2.get("price") for r2 in (i.get("results") or []) if r2.get("price")]
ps.sort()
if ps: print(f"competidores: {len(ps)} min={ps[0]} median={ps[len(ps)//2]} max={ps[-1]}")

# Try catalog publish at $649
TITLE=cp.get("name","")[:60]
print(f"title: '{TITLE}' ({len(TITLE)})")

payload={
  "title": TITLE,
  "catalog_product_id":cpid,
  "catalog_listing":True,
  "category_id":"MLM1271",  # Perfumes
  "price":649,
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
print(f"\nPOST catalog: {p.status_code}")
print(p.text[:1500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  print(f"\n✅ CATALOG CREATED {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
