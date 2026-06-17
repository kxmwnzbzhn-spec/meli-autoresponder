import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Titles inherited from CPID name (truncated to ≤60 if needed)
SPECS=[
  ("MLM42426004","Bocina Marshall Willen II Bluetooth IP67 Negro"),       # 47 chars
  ("MLM45472872","Bocina Marshall Willen Bluetooth Black And Grass Negro"),# 54 chars
]

results=[]
for CPID,TITLE in SPECS:
  print(f"\n=== {CPID} | title={TITLE} ({len(TITLE)} chars) ===")
  payload={
    "title": TITLE,
    "catalog_product_id":CPID,
    "catalog_listing":True,
    "category_id":"MLM59800",
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
    results.append((CPID,iid,d.get("title"),d.get("permalink")))
    print(f"  ✅ CREATED {iid} @ ${d.get('price')} status={d.get('status')}")
    print(f"  permalink: {d.get('permalink')}")
  else:
    print(f"  ERROR: {p.text[:600]}")

print("\n=== SUMMARY ===")
for c,i,t,u in results:
  print(f"  {c} → {i} @ $1999")
  print(f"    {u}")
