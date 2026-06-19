import os, requests, json, re
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Look up user_product first to get the right name + attributes
UP_ID="MLMU3423667933"
up=requests.get(f"{API}/user-products/{UP_ID}",headers=H,timeout=15).json()
print(f"user product: {up.get('name')}")
up_attrs={a["id"]:a.get("values",[{}])[0].get("name") for a in up.get("attributes",[])}
print(f"attrs: {up_attrs}")

# Try to find existing items associated with this user_product
ups=requests.get(f"{API}/user-products/{UP_ID}/items",headers=H,timeout=15)
print(f"\n/up/items: {ups.status_code}")
items=ups.json() if ups.status_code==200 else []
pic_urls=[]
for it in (items if isinstance(items,list) else [])[:1]:
  iid=it.get("id")
  print(f"  sample item {iid}")
  g=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
  for p in g.get("pictures",[])[:8]:
    u=p.get("secure_url") or p.get("url")
    if u: pic_urls.append(u)

# Fallback: search catalog products for Armaf Iconic to find CPID
if not pic_urls:
  pr=requests.get(f"{API}/products/search?status=active&site_id=MLM&q=Armaf+Club+Nuit+Iconic+105",headers=H,timeout=15)
  print(f"products/search: {pr.status_code}")
  for r2 in (pr.json().get("results") or [])[:5] if pr.status_code==200 else []:
    print(f"  product {r2.get('id')} {r2.get('name','')[:70]}")
    cp=requests.get(f"{API}/products/{r2.get('id')}",headers=H,timeout=15).json()
    for p in cp.get("pictures",[])[:6]:
      u=p.get("url")
      if u: pic_urls.append(u)
    if pic_urls: break

print(f"\npic urls collected: {len(pic_urls)}")

# Upload pics to our account
pic_ids=[]
for url in pic_urls[:6]:
  try:
    large=url.replace("-O.jpg","-F.jpg")
    rr=requests.get(large if large!=url else url,timeout=30)
    if rr.status_code==200 and len(rr.content)>10000:
      up_r=requests.post(f"{API}/pictures/items/upload",
        headers={"Authorization":f"Bearer {AT}"},
        files={"file":(f"armaf_{len(pic_ids)}.jpg",rr.content,"image/jpeg")},timeout=60)
      if up_r.status_code in (200,201):
        pid=up_r.json().get("id")
        if pid: pic_ids.append(pid); print(f"  ✓ {pid}")
  except Exception as e: print(f"  err: {e}")

# Title (≤60)
TITLE="Perfume Armaf Club De Nuit Iconic EDP 105ml Hombre"  # 51
print(f"\ntitle: '{TITLE}' ({len(TITLE)})")

desc=(
"PERFUME ARMAF CLUB DE NUIT ICONIC EAU DE PARFUM 105ML\n\n"
"Armaf Club de Nuit Iconic es una de las fragancias más reconocidas de "
"la línea Club de Nuit. Aroma masculino fresco, sofisticado y de larga "
"duración, ideal para uso diario y ocasiones formales.\n\n"
"PIRÁMIDE OLFATIVA\n"
"- Notas de salida: Bergamota, Limón, Manzana verde\n"
"- Notas de corazón: Pimienta negra, Pachulí, Geranio\n"
"- Notas de fondo: Ámbar, Vainilla, Almizcle, Maderas\n\n"
"CARACTERÍSTICAS\n"
"- Marca: Armaf (100% original)\n"
"- Línea: Club de Nuit\n"
"- Modelo: Iconic\n"
"- Tipo: Eau de Parfum (EDP)\n"
"- Tamaño: 105 ml / 3.6 oz\n"
"- Género: Hombre\n"
"- Duración estimada: 8-12 horas\n"
"- Estela: media-alta\n"
"- Presentación: frasco con caja sellada\n\n"
"100% ORIGINAL\n"
"Producto original de fábrica, empaque sellado. Envío inmediato desde "
"México. Garantía del vendedor 30 días contra defectos de fabricación."
)

attrs=[
  {"id":"BRAND","value_name":"Armaf"},
  {"id":"MODEL","value_name":"Iconic"},
  {"id":"LINE","value_name":"Club de Nuit"},
  {"id":"PERFUME_NAME","value_name":"Club de Nuit Iconic"},
  {"id":"GENDER","value_name":"Hombre"},
  {"id":"UNIT_VOLUME","value_name":"105 mL"},
  {"id":"ITEM_CONDITION","value_name":"Nuevo"},
  {"id":"FRAGRANCE_TYPE","value_name":"Eau de parfum"},
  {"id":"IS_ALCOHOL_FREE","value_name":"No"},
]
def ean13(p12):
  s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(p12))
  return p12+str((10-(s%10))%10)
attrs.append({"id":"GTIN","value_name":ean13("629104000048")})

payload={
  "title": TITLE,
  "category_id": "MLM1271",  # Perfumes
  "price": 649,
  "currency_id":"MXN",
  "available_quantity":1,
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
print(p.text[:2200])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
  print(f"\n✅ CREATED {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
