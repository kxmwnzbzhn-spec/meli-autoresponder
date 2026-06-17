import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Find JBL Go 4 CPID
s=requests.get(f"{API}/sites/MLM/search?q=JBL+Go+4&limit=5",headers=H,timeout=15).json()
go4_cpid=None
for r2 in s.get("results",[]):
  if r2.get("catalog_product_id"):
    title=(r2.get("title") or "").lower()
    if "go 4" in title or "go4" in title:
      go4_cpid=r2.get("catalog_product_id")
      print(f"found Go4 CPID via search: {go4_cpid} from item {r2.get('id')}")
      break

# Also try product search
if not go4_cpid:
  pr=requests.get(f"{API}/products/search?status=active&site_id=MLM&q=JBL+Go+4",headers=H,timeout=15)
  print(f"product search: {pr.status_code}")
  if pr.status_code==200:
    for r2 in pr.json().get("results",[])[:3]:
      print(f"  {r2.get('id')} {r2.get('name','')[:60]}")
      if "go 4" in (r2.get("name","") or "").lower() and not go4_cpid:
        go4_cpid=r2.get("id")

if not go4_cpid:
  go4_cpid="MLM44031244"  # known CPID for JBL Go 4 negro
print(f"using CPID: {go4_cpid}")

cp=requests.get(f"{API}/products/{go4_cpid}",headers=H,timeout=15).json()
print(f"CPID name: {cp.get('name')}")
pics=cp.get("pictures",[])[:8]
print(f"CPID pics: {len(pics)}")

pic_ids=[]
for p in pics:
  url=p.get("url")
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
          pic_ids.append(pid); print(f"  ✓ {pid}")
  except Exception as e:
    print(f"err: {e}")
print(f"\nuploaded: {len(pic_ids)}")

# Inspect COLOR attribute values for MLM59800
ats=requests.get(f"{API}/categories/MLM59800/attributes",headers=H,timeout=15).json()
color_a=next((a for a in ats if a.get("id")=="COLOR"),None)
if color_a:
  vs=color_a.get("values") or []
  print(f"\nCOLOR allowed: {len(vs)}")
  for v in vs[:20]:
    print(f"  {v.get('id')}: {v.get('name')}")

CAT="MLM59800"
TITLE="Bocina JBL Go 4 Bluetooth Usada Caja Abierta Color Aleatorio"
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

attrs=[
  {"id":"BRAND","value_name":"JBL"},
  {"id":"MODEL","value_name":"Go 4"},
  {"id":"ITEM_CONDITION","value_name":"Usado"},
  {"id":"WITH_BLUETOOTH","value_name":"Sí"},
  {"id":"IS_WATER_RESISTANT","value_name":"Sí"},
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
  "shipping":{"mode":"me2","free_shipping":True,"local_pick_up":False},
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
  print(f"\ndesc set: {pd.status_code}")
  print(f"\n✅ CREATED {iid} @ ${d.get('price')} status={d.get('status')}")
  print(f"shipping: {d.get('shipping')}")
  print(f"permalink: {d.get('permalink')}")
