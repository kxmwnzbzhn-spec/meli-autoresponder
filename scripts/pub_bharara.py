import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

SRC="MLM5516466768"
src=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
src_pics=src.get("pictures",[])
src_attrs=src.get("attributes",[])
pic_ids=[p.get("id") for p in src_pics if p.get("id")]
CAT=src.get("category_id") or "MLM59800"
CPID=src.get("catalog_product_id")
print(f"src CPID: {CPID}  pics: {len(pic_ids)}")

TITLE="Bocina Marshall Emberton Reacondicionada Calidad Excelente"
PRICE=1499
desc=(
"AVISO IMPORTANTE - LEE ANTES DE COMPRAR\n"
"==========================================\n"
"Esta bocina Marshall Emberton REACONDICIONADA NO ES COMPATIBLE con la "
"aplicacion oficial de Marshall (Marshall Bluetooth App). Al confirmar la "
"compra, el cliente declara haber leido y estar conforme con esta limitante "
"y NO podra presentarla como motivo de devolucion, reclamo o cancelacion.\n\n"
"El funcionamiento Bluetooth es 100% normal y se empareja directamente con "
"cualquier dispositivo (celular, tablet, laptop). Solo se pierde el acceso "
"a la app oficial de Marshall (ecualizador y firmware).\n"
"==========================================\n\n"
"PRODUCTO REACONDICIONADO - CALIDAD EXCELENTE\n\n"
"Esta unidad pertenece a nuestro grado PREMIUM dentro de los reacondicionados:\n"
"- Estado cosmetico EXCELENTE: minimas o nulas marcas de uso previo, "
"acabados limpios y completos.\n"
"- Funcionamiento al 100%, probada y certificada en banco de pruebas.\n"
"- Bateria recargable en optimas condiciones.\n"
"- Sonido potente y limpio, sin distorsion.\n"
"- Incluye cable de carga.\n"
"- Presentacion en caja generica de seguridad (no incluye caja Marshall "
"original).\n\n"
"DIFERENCIA CON OTRAS REACONDICIONADAS\n"
"Las bocinas REACONDICIONADAS CALIDAD EXCELENTE pasan una segunda revision "
"y solo se separan unidades que cumplen el estandar Premium. Por ello su "
"precio es ligeramente superior a las reacondicionadas estandar.\n\n"
"CARACTERISTICAS\n"
"- Conectividad: Bluetooth\n"
"- App oficial Marshall: NO COMPATIBLE\n"
"- Bateria recargable, larga duracion\n"
"- Sonido potente, 360 grados\n"
"- Color: negro\n"
"- Estado: reacondicionado calidad excelente\n\n"
"GARANTIA\n"
"30 dias del vendedor contra defectos de funcionamiento. NO aplica a: "
"incompatibilidad con app Marshall (declarada en este aviso), preferencias "
"esteticas subjetivas.\n\n"
"Al comprar este articulo, el cliente acepta expresamente lo anterior."
)

# Copy attributes EXCEPT ITEM_CONDITION (let condition field drive it)
keep=["BRAND","MODEL","LINE","COLOR","MAIN_COLOR","WITH_BLUETOOTH","IS_WATER_RESISTANT","CONNECTION_TYPE","GTIN"]
attrs=[]
for a in src_attrs:
  if a.get("id") in keep and a.get("value_name"):
    attrs.append({"id":a["id"],"value_name":a["value_name"]})

payload={
  "title": TITLE,
  "category_id": CAT,
  "price": PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_special",
  "condition":"used",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in pic_ids],
  "attributes": attrs + ([{"id":"GTIN","value_name":"7340055384230"}] if not any(a["id"]=="GTIN" for a in attrs) else []),
  "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False},
  "sale_terms":[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"}
  ],
  "description":{"plain_text":desc}
}
if CPID:
  payload["catalog_product_id"]=CPID

print(f"sending {len(attrs)} attrs, pics={len(pic_ids)}, condition=used")
p=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print("\nPOST /items:",p.status_code)
print(p.text[:2500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
  print(f"\ndesc set: {pd.status_code}")
  print(f"\n✅ CLONED {iid} @ ${PRICE} cond={d.get('condition')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
