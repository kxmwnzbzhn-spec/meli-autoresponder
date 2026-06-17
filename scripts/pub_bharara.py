import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM44710240"
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
name=cp.get("name","")
print(f"CPID name: {name}")
print(f"domain: {cp.get('domain_id')} pdp: {cp.get('pdp_types')}")
i=requests.get(f"{API}/products/{CPID}/items?limit=15",headers=H,timeout=15).json()
ps=[]
for r2 in (i.get("results") or [])[:15]:
  p=r2.get("price")
  if p: ps.append((p,r2.get("item_id"),r2.get("listing_type_id")))
ps.sort()
if ps:
  print(f"\ncompetidores: {len(ps)}")
  for pr,iid,lt in ps[:8]: print(f"  ${pr} | {iid} | {lt}")
  print(f"min/median/max: ${ps[0][0]} / ${ps[len(ps)//2][0]} / ${ps[-1][0]}")

TITLE=name[:60] if len(name)<=60 else "Bocina " + " ".join(name.split()[:8])
TITLE=TITLE[:60]
print(f"\ntitle: '{TITLE}' ({len(TITLE)})")

# Set initial price at ceiling 599 - lower if needed
START_PRICE=599
payload={
  "title": TITLE,
  "catalog_product_id":CPID,
  "catalog_listing":True,
  "category_id":"MLM59800",
  "price":START_PRICE,
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
print(f"\nPOST: {p.status_code}")
print(p.text[:1500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  print(f"\n✅ CREATED {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
