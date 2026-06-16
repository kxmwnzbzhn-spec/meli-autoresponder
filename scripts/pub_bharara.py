import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# =========================================
# 1) BHARARA VIKING BEIRUT $1500
# =========================================
print("=== BHARARA ===")
PICS=["963311-MLM112214145120_062026","611467-MLM113360496469_062026","827878-MLM113360996923_062026","893499-MLM112213513850_062026"]
CAT="MLM1271"
TITLE="Perfume Bharara Viking Beirut Parfum 100ml Hombre Mujer"
PRICE=1500
desc_bh=(
"Bharara Viking Beirut Parfum 100ml - Unisex\n\n"
"Bharara Beauty lanzo Viking Beirut en 2024. Una fragancia aromatica fresca y "
"sofisticada inspirada en Beirut. Composicion balanceada para hombre y mujer, "
"con larga duracion propia de un Parfum.\n\n"
"PIRAMIDE OLFATIVA\n"
"- Salida: Bergamota, Limon, Galbano\n"
"- Corazon: Notas ozonicas, Salvia, Geranio\n"
"- Fondo: Pachuli, Vetiver, Musgo de roble, Haba tonka\n\n"
"CARACTERISTICAS\n"
"- Tamano: 100ml / 3.4 oz\n"
"- Concentracion: Parfum (extracto)\n"
"- Duracion estimada: 8-12 horas\n"
"- Estela: media-alta\n"
"- Unisex\n\n"
"100% original. Envio inmediato. Garantia 30 dias."
)
def ean13(p12):
  s=sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(p12))
  return p12+str((10-(s%10))%10)
attrs_bh=[
  {"id":"BRAND","value_name":"Bharara"},
  {"id":"MODEL","value_name":"Viking Beirut"},
  {"id":"LINE","value_name":"Viking"},
  {"id":"PERFUME_NAME","value_name":"Viking Beirut"},
  {"id":"UNIT_VOLUME","value_name":"100 mL"},
  {"id":"GENDER","value_name":"Sin género"},
  {"id":"ITEM_CONDITION","value_name":"Nuevo"},
  {"id":"GTIN","value_name":ean13("786000000003")},
]
pay_bh={
  "title": TITLE, "category_id": CAT, "price": PRICE,
  "currency_id":"MXN","available_quantity":1,"listing_type_id":"gold_special",
  "condition":"new","buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in PICS],
  "attributes": attrs_bh,
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc_bh}
}
pb=requests.post(f"{API}/items",headers=HJ,json=pay_bh,timeout=30)
print("Bharara POST:",pb.status_code)
print(pb.text[:1200])
bharara_id=None
if pb.status_code==201:
  d=pb.json()
  bharara_id=d.get("id")
  print(f"\n✅ Bharara CREATED {bharara_id} @ ${PRICE} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
  # set description via POST
  pd=requests.post(f"{API}/items/{bharara_id}/description",headers=HJ,json={"plain_text":desc_bh},timeout=20)
  print(f"desc set: {pd.status_code}")

# =========================================
# 2) JBL CLIP 5 NEGRO CPID MLM37110181 - $999
# =========================================
print("\n=== JBL CLIP 5 ===")
CPID="MLM37110181"
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
print(f"CPID name: {cp.get('name')}")
print(f"buy_box: {cp.get('buy_box_winner')}")
print(f"domain: {cp.get('domain_id')} pdp_types: {cp.get('pdp_types')}")

CAT_JBL="MLM59800"  # Bocinas (Marshall used this too)
PRICE_JBL=999
TITLE_JBL="Bocina Portátil JBL Clip 5 Bluetooth Negro"  # 43 chars

pay_jbl={
  "title": TITLE_JBL,
  "catalog_product_id": CPID,
  "catalog_listing": True,
  "category_id": CAT_JBL,
  "price": PRICE_JBL,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_pro",
  "condition":"new",
  "buying_mode":"buy_it_now",
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ]
}
pj=requests.post(f"{API}/items",headers=HJ,json=pay_jbl,timeout=30)
print("JBL POST:",pj.status_code)
print(pj.text[:1200])
if pj.status_code==201:
  d=pj.json()
  jbl_id=d.get("id")
  print(f"\n✅ JBL CREATED {jbl_id} @ ${PRICE_JBL} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
