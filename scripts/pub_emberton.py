import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# 1) Close old catalog listing
OLD="MLM5516465680"
c1=requests.put(f"{API}/items/{OLD}",headers=H,json={"status":"paused"},timeout=20)
print(f"PAUSE {OLD}:",c1.status_code,c1.text[:200])
c2=requests.put(f"{API}/items/{OLD}",headers=H,json={"status":"closed"},timeout=20)
print(f"CLOSE {OLD}:",c2.status_code,c2.text[:200])

# 2) Get pics from CPID for tradicional
CPID="MLM42230166"
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
pics=cp.get("pictures",[])[:8]
pic_urls=[{"source":p.get("url")} for p in pics if p.get("url")]
print(f"pics from CPID: {len(pic_urls)}")

PRICE=1999
TITLE="Bocina Marshall Emberton Inalámbrica Bluetooth Negro"  # 53 chars

payload={
  "title": TITLE,
  "catalog_product_id": CPID,  # tradicional asociado a CPID
  "category_id":"MLM59800",
  "price":PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_special",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "pictures": pic_urls,
  "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                {"id":"WARRANTY_TIME","value_name":"30 días"}],
  "description":{"plain_text":"Bocina Marshall Emberton Bluetooth portátil. Sonido potente, batería recargable, color negro. Producto nuevo, garantía 30 días."}
}
p=requests.post(f"{API}/items",headers=H,json=payload,timeout=30)
print("POST /items:",p.status_code)
print(p.text[:1500])
if p.status_code==201:
  d=p.json()
  print(f"\nCREATED {d.get('id')} @ ${PRICE} status={d.get('status')} permalink={d.get('permalink')}")
