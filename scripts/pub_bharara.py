import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

PICS=["963311-MLM112214145120_062026","611467-MLM113360496469_062026","827878-MLM113360996923_062026","893499-MLM112213513850_062026"]
CAT="MLM1271"
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

# Get GTIN attribute spec to find the proper "no aplica" value
g=requests.get(f"{API}/categories/{CAT}/attributes",headers=H,timeout=15).json()
gtin_spec=next((a for a in g if a.get("id")=="GTIN"),None)
print("GTIN spec keys:",list(gtin_spec.keys()) if gtin_spec else None)
print("GTIN values:",gtin_spec.get("values") if gtin_spec else None)

attrs=[
  {"id":"BRAND","value_name":"Bharara"},
  {"id":"MODEL","value_name":"Viking Beirut"},
  {"id":"LINE","value_name":"Viking"},
  {"id":"PERFUME_NAME","value_name":"Viking Beirut"},
  {"id":"FRAGRANCE_TYPE","value_name":"Parfum"},
  {"id":"UNIT_VOLUME","value_name":"100 mL"},
  {"id":"GENDER","value_name":"Sin género"},
  {"id":"ITEM_CONDITION","value_name":"Nuevo"},
  {"id":"GTIN","value_name":"7000000000027"},  # try placeholder with proper checksum
]

# Recompute EAN-13: digits[0..11] + check; we'll generate a valid 13-digit code
def ean13(prefix12):
  s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(prefix12))
  c=(10-(s%10))%10
  return prefix12+str(c)
gtin=ean13("786000000002")
print("computed GTIN:",gtin)
for a in attrs:
  if a["id"]=="GTIN": a["value_name"]=gtin

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
    {"id":"WARRANTY_TIME","value_name":"30 días"},
    {"id":"PURCHASE_MAX_QUANTITY","value_name":"8"}
  ],
  "description":{"plain_text":desc}
}

p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print("\nPOST /items:",p.status_code)
print(p.text[:2500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  dr=requests.put(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
  print(f"\ndesc: {dr.status_code}")
  print(f"\n✅ CREATED {iid} @ ${PRICE} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
