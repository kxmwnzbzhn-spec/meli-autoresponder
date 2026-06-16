import os, re, json, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Reuse uploaded pic IDs from prior run
PICS=["963311-MLM112214145120_062026","611467-MLM113360496469_062026","827878-MLM113360996923_062026","893499-MLM112213513850_062026"]

CAT="MLM1271"  # Perfumes
# Get valid attrs for MLM1271
ats=requests.get(f"{API}/categories/{CAT}/attributes",headers=H,timeout=15).json()
valid_ids=set(a["id"] for a in ats)
print(f"valid attrs for {CAT}: {len(valid_ids)}")
for a in ats:
  if a.get("tags",{}).get("required"):
    print(f"  REQ {a['id']} ({a.get('name')}) type={a.get('value_type')}")

TITLE="Perfume Bharara Viking Beirut Parfum 100ml Hombre Mujer"
PRICE=1500
desc=(
"Bharara Viking Beirut Parfum 100ml — Unisex\n\n"
"Bharara Beauty lanzó Viking Beirut en 2024. Una fragancia aromática fresca y "
"sofisticada inspirada en Beirut, ciudad mediterránea. Composición olfativa "
"balanceada para hombre y mujer, con larga duración propia de un Parfum.\n\n"
"PIRÁMIDE OLFATIVA\n"
"• Salida: Bergamota, Limón, Gálbano\n"
"• Corazón: Notas ozónicas, Salvia, Geranio\n"
"• Fondo: Pachulí, Vetiver, Musgo de roble, Haba tonka\n\n"
"CARACTERÍSTICAS\n"
"• Tamaño: 100ml / 3.4 oz\n"
"• Concentración: Parfum (extracto, mayor a EDP)\n"
"• Duración estimada: 8-12 horas\n"
"• Estela: media-alta\n"
"• Unisex: ideal para hombre y mujer\n"
"• Presentación: frasco original sellado con caja\n\n"
"100% original. Envío inmediato desde México. Garantía vendedor 30 días."
)

candidate_attrs=[
  ("BRAND","Bharara"),
  ("MODEL","Viking Beirut"),
  ("LINE","Viking"),
  ("GENDER","Sin género"),
  ("ITEM_CONDITION","Nuevo"),
  ("FRAGRANCE_TYPE","Parfum"),
  ("UNIT_VOLUME","100 mL"),
  ("VOLUME_CAPACITY","100 mL"),
  ("PRESENTATION_TYPE","Estuche"),
  ("AGE_GROUP","Adultos"),
  ("MAIN_COLOR","Multicolor"),
]
attrs=[{"id":i,"value_name":v} for i,v in candidate_attrs if i in valid_ids]
print(f"sending {len(attrs)} attrs")

payload={
  "title": TITLE,
  "category_id": CAT,
  "price": PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_special",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in PICS],
  "attributes": attrs,
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc}
}

p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print("\nPOST /items:",p.status_code)
print(p.text[:2500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  # Set description separately if needed
  dr=requests.put(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
  print(f"\nset description: {dr.status_code}")
  print(f"\n✅ CREATED {iid} @ ${PRICE} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
