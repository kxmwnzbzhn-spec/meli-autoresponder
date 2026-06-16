import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# 1) Close NEW tradicional $1999 (the one we just published) so we don't duplicate
PREV="MLM5516466202"
p1=requests.put(f"{API}/items/{PREV}",headers=H,json={"status":"paused"},timeout=20)
print(f"PAUSE {PREV}:",p1.status_code,p1.text[:200])
p2=requests.put(f"{API}/items/{PREV}",headers=H,json={"status":"closed"},timeout=20)
print(f"CLOSE {PREV}:",p2.status_code,p2.text[:200])

# 2) Try to close catalog $3000 once more
OLD="MLM5516465680"
o1=requests.put(f"{API}/items/{OLD}",headers=H,json={"deleted":"true"},timeout=20)
print(f"DELETE {OLD}:",o1.status_code,o1.text[:200])
od=requests.delete(f"{API}/items/{OLD}",headers=H,timeout=20)
print(f"HTTP-DELETE {OLD}:",od.status_code,od.text[:200])

# 3) Publish tradicional REFURBISHED $1999
CPID="MLM42230166"
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
pics=cp.get("pictures",[])[:8]
pic_urls=[{"source":p.get("url")} for p in pics if p.get("url")]
print(f"pics: {len(pic_urls)}")

PRICE=1999
TITLE="Bocina Marshall Emberton Bluetooth Reacondicionada Negro"  # 56 chars

# Try condition refurbished
payload={
  "title": TITLE,
  "catalog_product_id": CPID,
  "category_id":"MLM59800",
  "price":PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_special",
  "condition":"refurbished",
  "buying_mode":"buy_it_now",
  "pictures": pic_urls,
  "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                {"id":"WARRANTY_TIME","value_name":"30 días"}],
  "description":{"plain_text":"Bocina Marshall Emberton Bluetooth portátil REACONDICIONADA. Producto remanufacturado, probado y certificado en perfecto funcionamiento. Sonido potente, batería recargable, color negro. Garantía 30 días."}
}
p=requests.post(f"{API}/items",headers=H,json=payload,timeout=30)
print("POST refurbished:",p.status_code)
print(p.text[:1800])
if p.status_code==201:
  d=p.json()
  print(f"\nCREATED REFURBISHED {d.get('id')} @ ${PRICE} cond={d.get('condition')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
