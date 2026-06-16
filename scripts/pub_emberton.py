import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM42230166"
PRICE=3000

payload={
  "catalog_product_id":CPID,
  "catalog_listing":True,
  "category_id":"MLM59800",
  "price":PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_pro",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                {"id":"WARRANTY_TIME","value_name":"30 días"}]
}
print("payload:",json.dumps(payload))
p=requests.post(f"{API}/items",headers=H,json=payload,timeout=30)
print("POST /items:",p.status_code)
print(p.text[:1500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  print(f"\nCREATED {iid} @ ${PRICE}  status={d.get('status')}  permalink={d.get('permalink')}")
