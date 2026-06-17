import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM43009587"
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
name=cp.get("name","")
print(f"CPID name: {name}")
print(f"domain: {cp.get('domain_id')} pdp: {cp.get('pdp_types')}")

# Snapshot
i=requests.get(f"{API}/products/{CPID}/items?limit=15",headers=H,timeout=15).json()
ps=[]
for r2 in (i.get("results") or []):
  p=r2.get("price")
  if p: ps.append(p)
ps.sort()
if ps:
  print(f"competidores: {len(ps)} min={ps[0]} median={ps[len(ps)//2]} max={ps[-1]}")

# Title: try truncating name to ≤60
TITLE=name
if len(TITLE)>60:
  TITLE=TITLE[:57]+"..."
# better SEO
if "Marshall" in name or "Emberton" in name or "Willen" in name:
  TITLE="Bocina " + " ".join(name.split()[:8])
  TITLE=TITLE[:60]
print(f"title: '{TITLE}' ({len(TITLE)} chars)")

payload={
  "title": TITLE,
  "catalog_product_id":CPID,
  "catalog_listing":True,
  "category_id":"MLM59800",
  "price":2499,
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
print(f"POST: {p.status_code}")
print(p.text[:1500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  print(f"\n✅ CREATED {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
