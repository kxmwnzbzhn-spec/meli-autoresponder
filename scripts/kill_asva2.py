import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

OLD="MLM3035213185"
CPID="MLM52113823"
TARGET_CAT="MLM456032"  # Esoterismo > Perfumes

# 1) Get all data from CPID + old item
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
TITLE=cp.get("name","Perfume The Alchemia Lab Flor De Nopal Mexico En La Piel 100ml")[:60]
print(f"title: {TITLE}")

# Upload photos from CPID
pic_ids=[]
for p in cp.get("pictures",[])[:8]:
  url=(p.get("url") or "").replace("-O.jpg","-F.jpg")
  try:
    rr=requests.get(url,timeout=30)
    if rr.status_code==200 and len(rr.content)>10000:
      up=requests.post(f"{API}/pictures/items/upload",headers={"Authorization":f"Bearer {AT}"},
        files={"file":(f"eso_{len(pic_ids)}.jpg",rr.content,"image/jpeg")},timeout=60)
      if up.status_code in (200,201):
        pid=up.json().get("id")
        if pid: pic_ids.append(pid)
  except: pass
print(f"pics: {len(pic_ids)}")

# 2) Check required attrs for MLM456032
ats=requests.get(f"{API}/categories/{TARGET_CAT}/attributes",headers=H,timeout=15).json()
valid={a["id"]:a for a in ats}
print(f"cat attrs: {len(valid)}")
for a in ats:
  if a.get("tags",{}).get("required") or a.get("tags",{}).get("catalog_required"):
    print(f"  REQ {a['id']} ({a.get('name')}) type={a.get('value_type')}")

# 3) Cierre el viejo
print("\n=== Cerrar MLM3035213185 ===")
for action in [{"available_quantity":0},{"status":"paused"},{"status":"closed"},{"deleted":"true"}]:
  requests.put(f"{API}/items/{OLD}",headers=HJ,json=action,timeout=20)
g=requests.get(f"{API}/items/{OLD}?attributes=id,status,sub_status",headers=H,timeout=15).json()
print(f"  → {g.get('status')} {g.get('sub_status')}")

# 4) Publish nuevo tradicional en MLM456032
desc=("Perfume The Alchemia Lab Flor de Nopal — México en la Piel. Eau de Parfum 100 ml unisex. "
      "Fragancia con notas terrosas y florales que evocan la naturaleza mexicana. Ideal para uso ritual, "
      "espiritual o personal. Producto original, sellado. Envío inmediato. Garantía del vendedor 30 días.")

attrs=[
  {"id":"BRAND","value_name":"The Alchemia Lab"},
  {"id":"MODEL","value_name":"Flor de Nopal"},
  {"id":"LINE","value_name":"México en la Piel"},
  {"id":"ITEM_CONDITION","value_name":"Nuevo"},
  {"id":"GENDER","value_name":"Sin género"},
  {"id":"UNIT_VOLUME","value_name":"100 mL"},
  {"id":"FRAGRANCE_TYPE","value_name":"Eau de parfum"},
  {"id":"PERFUME_NAME","value_name":"Flor de Nopal"},
]
attrs=[a for a in attrs if a["id"] in valid]

payload={
  "title": TITLE,
  "category_id": TARGET_CAT,
  "price": 999,
  "currency_id":"MXN",
  "available_quantity":50,
  "listing_type_id":"gold_special",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in pic_ids],
  "attributes": attrs,
  "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False},
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc}
}
p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"\nPOST: {p.status_code}")
print(p.text[:1500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
  print(f"\n✅ CREATED {iid} @ ${d.get('price')} cat={d.get('category_id')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
