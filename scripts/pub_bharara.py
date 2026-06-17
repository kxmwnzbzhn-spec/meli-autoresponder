import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CAT="MLM194118"  # Calcetas y Calcetines (leaf)
PICS=["834576-MLM113409938965_062026","765596-MLM113410408307_062026","630176-MLM112259910322_062026","642469-MLM112259910344_062026","911512-MLM113409969181_062026"]

TITLE="Calcetines Tommy Hilfiger Hombre Pack 3 Pares Negro Algodón"
desc=(
"CALCETINES TOMMY HILFIGER PARA HOMBRE - PACK DE 3 PARES NEGRO\n\n"
"Set de 3 pares de calcetines Tommy Hilfiger color negro, tejido en mezcla "
"premium de algodón con elastano para máxima comodidad y durabilidad. "
"Diseño clásico atemporal ideal para uso diario, oficina, deporte casual "
"y ocasiones formales.\n\n"
"CARACTERÍSTICAS\n"
"- Marca: Tommy Hilfiger (100% original)\n"
"- Pack: 3 pares por set\n"
"- Color: Negro sólido\n"
"- Material: Mezcla de algodón premium con elastano\n"
"- Talla: Estándar adulto, ajuste universal (talla 7-12 MX)\n"
"- Tipo: Calcetín pantorrillero (3/4)\n"
"- Logo: Bordado clásico Tommy Hilfiger\n"
"- Tejido transpirable y suave al tacto\n"
"- Costuras planas anti-rozaduras\n"
"- Banda elástica reforzada que no aprieta\n"
"- Refuerzo en talón y puntera para mayor durabilidad\n\n"
"USOS RECOMENDADOS\n"
"- Trabajo y oficina\n"
"- Uso diario casual\n"
"- Deporte ligero\n"
"- Ocasiones semi-formales\n"
"- Ideal para regalo\n\n"
"CUIDADOS\n"
"- Lavar a máquina con agua fría\n"
"- No usar blanqueador\n"
"- Secar al aire para máxima durabilidad\n"
"- Plancha a baja temperatura si es necesario\n\n"
"PRODUCTO ORIGINAL TOMMY HILFIGER\n"
"100% originales con etiquetas de marca. Empaque sellado de fábrica. "
"Envío inmediato desde México. Garantía del vendedor 30 días por defectos "
"de fabricación."
)

attrs=[
  {"id":"BRAND","value_name":"Tommy Hilfiger"},
  {"id":"MODEL","value_name":"Pack 3 Pares"},
  {"id":"COLOR","value_name":"Negro"},
  {"id":"SIZE","value_name":"Único"},
  {"id":"GENDER","value_id":"339666","value_name":"Hombre"},
  {"id":"SOCKS_TYPE","value_id":"44992001","value_name":"Pantorrillero"},
  {"id":"LENGTH_TYPE","value_id":"2150772","value_name":"3/4"},
  {"id":"MAIN_COLOR","value_id":"2450295","value_name":"Negro"},
  {"id":"ITEM_CONDITION","value_name":"Nuevo"},
  {"id":"MAIN_MATERIAL","value_name":"Algodón"},
  {"id":"UNITS_PER_PACK","value_name":"3"},
]

payload={
  "title": TITLE,
  "category_id": CAT,
  "price": 199,
  "currency_id":"MXN",
  "available_quantity":100,
  "listing_type_id":"gold_special",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in PICS],
  "attributes": attrs,
  "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False},
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc}
}

p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"POST: {p.status_code}")
print(p.text[:2500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
  print(f"\ndesc: {pd.status_code}")
  print(f"\n✅ CREATED {iid} @ ${d.get('price')} qty={d.get('available_quantity')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
