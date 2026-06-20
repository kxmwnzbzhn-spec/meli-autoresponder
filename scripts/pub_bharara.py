import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM70246080"
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
name=cp.get("name","")
parent=cp.get("parent_id")
print(f"name: {name}")
print(f"domain: {cp.get('domain_id')} pdp: {cp.get('pdp_types')} parent: {parent}")
print(f"pics: {len(cp.get('pictures',[]))}")

# Competition
i=requests.get(f"{API}/products/{CPID}/items?limit=15",headers=H,timeout=15).json()
ps=[r2.get("price") for r2 in (i.get("results") or []) if r2.get("price")]
ps.sort()
if ps: print(f"competidores: {len(ps)} min={ps[0]} median={ps[len(ps)//2]} max={ps[-1]}")
else: print("sin competidores activos")

# Find category from competitor item or domain
cat="MLM59800"  # default bocinas
if (cp.get("domain_id") or "").endswith("PERFUMES"): cat="MLM1271"
for r2 in (i.get("results") or [])[:3]:
  iid=r2.get("item_id")
  if iid:
    try:
      ci=requests.get(f"{API}/items/{iid}?attributes=category_id",headers=H,timeout=10).json()
      if ci.get("category_id"): cat=ci["category_id"]; break
    except: pass
print(f"category_id: {cat}")

TITLE=name[:60] if len(name)<=60 else ("Bocina " + " ".join(name.split()[:8]))[:60]
print(f"title: '{TITLE}' ({len(TITLE)})")

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
print(f"\nPOST: {p.status_code}")
print(p.text[:1500])
if p.status_code==201:
  d=p.json()
  print(f"\n✅ CREATED {d.get('id')} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
