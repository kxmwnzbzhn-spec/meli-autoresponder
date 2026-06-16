import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
  "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM42230166"
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
pics=cp.get("pictures",[])[:8]
pic_urls=[{"source":p.get("url")} for p in pics if p.get("url")]

PRICE=1999
TITLE="Bocina Marshall Emberton Bluetooth Reacondicionada Negro"  # 56

payload={
  "title": TITLE,
  "catalog_product_id": CPID,
  "category_id":"MLM59800",
  "price":PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_special",
  "condition":"used",   # MELI MLM59800 no acepta refurbished; usa used + marca claramente en título/desc
  "buying_mode":"buy_it_now",
  "pictures": pic_urls,
  "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                {"id":"WARRANTY_TIME","value_name":"30 días"}],
  "description":{"plain_text":(
    "PRODUCTO REACONDICIONADO / REMANUFACTURADO.\n\n"
    "Bocina Marshall Emberton Bluetooth portátil, color negro. "
    "Reacondicionada de fábrica: probada, limpia y certificada en funcionamiento óptimo. "
    "Puede presentar mínimos detalles cosméticos por uso previo. "
    "Funcionamiento al 100%. Batería recargable. Sonido potente. "
    "Incluye cable de carga.\n\n"
    "Garantía del vendedor: 30 días contra defectos de funcionamiento."
  )}
}
p=requests.post(f"{API}/items",headers=H,json=payload,timeout=30)
print("POST used/reacond:",p.status_code)
print(p.text[:1500])
if p.status_code==201:
  d=p.json()
  print(f"\nCREATED {d.get('id')} @ ${PRICE} cond={d.get('condition')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
