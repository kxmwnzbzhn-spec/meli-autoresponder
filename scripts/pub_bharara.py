import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Source item for pics: MLM3002914461 (JBL Go4 Negro)
SRC="MLM3002914461"
src=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
src_pics=src.get("pictures",[])
print(f"src pics: {len(src_pics)}")
print(f"src category: {src.get('category_id')}")
print(f"src catalog_product_id: {src.get('catalog_product_id')}")

# Re-upload to our account (avoid permission/CORS issues)
pic_ids=[]
for pp in src_pics[:8]:
    url=pp.get("secure_url") or pp.get("url")
    if not url: continue
    try:
        rr=requests.get(url,timeout=30)
        if rr.status_code==200 and len(rr.content)>5000:
            up=requests.post(f"{API}/pictures/items/upload",
                headers={"Authorization":f"Bearer {AT}"},
                files={"file":(f"go4_{len(pic_ids)}.jpg",rr.content,"image/jpeg")},timeout=60)
            if up.status_code in (200,201):
                pid=up.json().get("id")
                if pid:
                    pic_ids.append(pid)
                    print(f"  ✓ pic {pid}")
            else:
                print(f"  ✗ upload {up.status_code} {up.text[:200]}")
    except Exception as e:
        print(f"  err: {e}")
print(f"\nuploaded pics: {len(pic_ids)}")

CAT="MLM59800"  # Bocinas
TITLE="Bocina JBL Go 4 Bluetooth Usada Caja Abierta Color Aleatorio"  # 60 chars exactly
print(f"title len: {len(TITLE)}")

desc=(
"==============================================\n"
"COLOR ALEATORIO - NO SE PUEDE ELEGIR EL COLOR\n"
"==============================================\n\n"
"IMPORTANTE: El color de la bocina es totalmente aleatorio y NO se puede "
"escoger. El cliente recibira el color disponible al momento de empaquetar. "
"Al confirmar la compra acepta esta condicion y NO podra presentarla como "
"motivo de devolucion, reclamo o cancelacion.\n\n"
"==============================================\n"
"PRODUCTO USADO - CAJA ABIERTA - LIQUIDACION\n"
"==============================================\n\n"
"Bocina JBL Go 4 Bluetooth en condicion USADA / CAJA ABIERTA. Producto "
"proveniente de devoluciones liquidadas a super precio.\n\n"
"ESTADO DEL PRODUCTO\n"
"- La bocina puede estar en perfecto estado o presentar minimos detalles "
"esteticos por uso previo.\n"
"- La caja puede estar en perfecto estado, ligeramente danada, abierta o "
"con marcas de manipulacion.\n"
"- Puede o no incluir etiquetas de envios anteriores en la caja externa.\n"
"- Funcionamiento al 100% garantizado: Bluetooth, sonido, bateria y "
"resistencia al agua IP67.\n"
"- NO COMPATIBLE con la aplicacion oficial de JBL Portable. Al comprar el "
"cliente acepta esta limitante y no podra reclamar por la app.\n\n"
"CARACTERISTICAS\n"
"- Conectividad: Bluetooth\n"
"- Resistencia: IP67 polvo y agua\n"
"- Bateria recargable\n"
"- Tamano compacto, portatil\n"
"- Color: ALEATORIO (no se elige)\n"
"- Condicion: usada / caja abierta\n"
"- App oficial JBL: NO COMPATIBLE\n\n"
"GARANTIA\n"
"30 dias del vendedor contra defectos de funcionamiento. NO aplica para: "
"color especifico, estado cosmetico, condicion de caja, etiquetas de envios "
"previos, incompatibilidad con app JBL. Estas condiciones quedan declaradas "
"en este aviso y son aceptadas con la compra.\n\n"
"100% funcional. Excelente producto a un excelente super precio."
)

# Attempt 1: tradicional + condition=used + free shipping
attrs=[
  {"id":"BRAND","value_name":"JBL"},
  {"id":"MODEL","value_name":"Go 4"},
  {"id":"LINE","value_name":"Go"},
  {"id":"ITEM_CONDITION","value_name":"Usado"},
  {"id":"COLOR","value_name":"Multicolor"},
  {"id":"MAIN_COLOR","value_name":"Multicolor"},
  {"id":"WITH_BLUETOOTH","value_name":"Sí"},
  {"id":"IS_WATER_RESISTANT","value_name":"Sí"},
  {"id":"WATER_PROOF_GRADE","value_name":"IP67"},
]

payload={
  "title": TITLE,
  "category_id": CAT,
  "price": 299,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_special",
  "condition":"used",
  "buying_mode":"buy_it_now",
  "pictures":[{"id":p} for p in pic_ids],
  "attributes": attrs,
  "shipping":{"mode":"me2","free_shipping":True,"local_pick_up":False,"tags":["self_service_in"]},
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
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
  print(f"\ndesc: {pd.status_code}")
  print(f"\n✅ CREATED {iid} @ ${d.get('price')} cond={d.get('condition')} status={d.get('status')}")
  print(f"shipping: {d.get('shipping')}")
  print(f"permalink: {d.get('permalink')}")
