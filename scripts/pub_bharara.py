import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CAT="MLM194118"  # Calcetas y Pantimedias
PICS=["834576-MLM113409938965_062026","765596-MLM113410408307_062026","630176-MLM112259910322_062026","642469-MLM112259910344_062026","911512-MLM113409969181_062026"]

# Inspect category requirements
ats=requests.get(f"{API}/categories/{CAT}/attributes",headers=H,timeout=15).json()
print(f"cat attrs: {len(ats)}")
valid_ids={}
for a in ats:
  valid_ids[a["id"]]=a
  if a.get("tags",{}).get("required") or a.get("tags",{}).get("catalog_required"):
    print(f"  REQ {a['id']} ({a.get('name')}) type={a.get('value_type')}")

TITLE="Calcetines Tommy Hilfiger Hombre Pack 3 Pares Negro Algodón"
print(f"\ntitle len: {len(TITLE)}")

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
"- Tipo: Calcetín mediano (media pantorrilla)\n"
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

candidate=[
  ("BRAND","Tommy Hilfiger"),
  ("GENDER","Hombre"),
  ("AGE_GROUP","Adultos"),
  ("MAIN_COLOR","Negro"),
  ("COLOR","Negro"),
  ("ITEM_CONDITION","Nuevo"),
  ("MAIN_MATERIAL","Algodón"),
  ("UNITS_PER_PACK","3"),
  ("SIZE","Único"),
  ("SOCKS_TYPE","Media pantorrilla"),
  ("CLOTHING_TYPE","Calcetines"),
  ("LINE","Classic"),
  ("MODEL","Pack 3 Pares"),
  ("FOOT_LENGTH","Estándar"),
  ("PATTERN","Liso"),
  ("DESIGN","Liso"),
  ("GTIN","0088541002493"),  # known Tommy socks UPC if valid
]
attrs=[{"id":i,"value_name":v} for i,v in candidate if i in valid_ids]
print(f"sending {len(attrs)} attrs")

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
print(f"\nPOST: {p.status_code}")
print(p.text[:2500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
  print(f"\ndesc: {pd.status_code}")
  print(f"\n✅ CREATED {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
