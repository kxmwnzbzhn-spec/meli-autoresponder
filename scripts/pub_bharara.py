import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# STEP 1: Evaluate ALL 3 CPID candidates
print("=== EVALUATING 3 CPID CANDIDATES ===")
candidates=["MLM45208170","MLM68807508","MLM28067123"]
scored=[]
for cpid in candidates:
  cp=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
  name=cp.get("name","")
  pdp=cp.get("pdp_types",[])
  pics=len(cp.get("pictures",[]))
  attrs={a.get("id"):a.get("value_name") for a in cp.get("attributes",[])}
  i=requests.get(f"{API}/products/{cpid}/items?limit=15",headers=H,timeout=15).json()
  total_items=i.get("paging",{}).get("total",0)
  ps=[r2.get("price") for r2 in (i.get("results") or []) if r2.get("price")]
  ps.sort()
  print(f"\n{cpid}: '{name}'")
  print(f"  pdp_types={pdp} pics={pics} total_competidores={total_items}")
  print(f"  unit_volume={attrs.get('UNIT_VOLUME')} gender={attrs.get('GENDER')} fragrance={attrs.get('FRAGRANCE_TYPE')}")
  if ps: print(f"  prices min={ps[0]} median={ps[len(ps)//2]} max={ps[-1]}")
  scored.append((cpid,total_items,pics,name,attrs))

# Pick the CPID with most competitors and pics (most "real" / official)
scored.sort(key=lambda x:(x[1],x[2]),reverse=True)
chosen=scored[0]
CPID=chosen[0]
print(f"\n>>> CHOSEN CPID: {CPID} ({chosen[3]}) | competidores={chosen[1]} pics={chosen[2]}")

# STEP 2: Close the wrong tradicional
print("\n=== CLOSING WRONG TRADICIONAL MLM3031473511 ===")
OLD="MLM3031473511"
for action in [{"available_quantity":0},{"status":"paused"},{"status":"closed"},{"deleted":"true"}]:
  p=requests.put(f"{API}/items/{OLD}",headers=HJ,json=action,timeout=20)
  print(f"  {list(action.keys())[0]}={list(action.values())[0]}: {p.status_code}")
g=requests.get(f"{API}/items/{OLD}?attributes=id,status,sub_status",headers=H,timeout=15).json()
print(f"OLD final: {g}")

# STEP 3: Publish CATALOG on chosen CPID
print(f"\n=== PUBLISHING CATALOG ON {CPID} @ $649 ===")
payload={
  "catalog_product_id": CPID,
  "catalog_listing": True,
  "category_id":"MLM1271",
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
pp=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"POST: {pp.status_code}")
print(pp.text[:1500])
if pp.status_code==201:
  d=pp.json()
  iid=d.get("id")
  print(f"\n✅ CATALOG CREATED {iid} @ ${d.get('price')} status={d.get('status')} CPID={d.get('catalog_product_id')}")
  print(f"permalink: {d.get('permalink')}")
