import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

RT_A=os.environ["MELI_REFRESH_TOKEN_AH"]
ra=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT_A},timeout=20)
AT_A=ra.json()["access_token"]
HA={"Authorization":f"Bearer {AT_A}"}
HJA={"Authorization":f"Bearer {AT_A}","Content-Type":"application/json"}

# Re-upload pics from JBL Charge 6 official CPID (MLM50444272) — high resolution
CPID_PICS="MLM50444272"
cp=requests.get(f"{API}/products/{CPID_PICS}",headers=HA,timeout=15).json()
pic_ids=[]
for pp in cp.get("pictures",[])[:8]:
  url=pp.get("url")
  if not url: continue
  # MELI URLs end with -O.jpg for original size. Convert to higher res if pattern allows
  url_max=url.replace("-O.jpg","-F.jpg")  # F = large
  for try_url in [url_max, url]:
    try:
      rr=requests.get(try_url,timeout=30)
      if rr.status_code==200 and len(rr.content)>10000:
        up=requests.post(f"{API}/pictures/items/upload",
          headers={"Authorization":f"Bearer {AT_A}"},
          files={"file":(f"c_{len(pic_ids)}.jpg",rr.content,"image/jpeg")},timeout=60)
        if up.status_code in (200,201):
          pid=up.json().get("id")
          if pid: 
            pic_ids.append(pid)
            print(f"  ✓ {pid} from {try_url[:80]}")
            break
        else:
          print(f"  ✗ upload {up.status_code} {up.text[:200]}")
    except Exception as e:
      print(f"  err: {e}")
print(f"\nuploaded: {len(pic_ids)}")

TITLE="JBL Charge 6 Bocina Bluetooth IP67 Reacondicionada Negro"
PRICE=599
desc=(
"AVISO IMPORTANTE - LEE ANTES DE COMPRAR\n"
"==========================================\n"
"Esta bocina JBL Charge 6 REACONDICIONADA NO ES COMPATIBLE con la "
"aplicacion oficial de JBL Portable. Al confirmar la compra, el cliente "
"declara haber leido y estar conforme con esta limitante y NO podra "
"presentarla como motivo de devolucion, reclamo o cancelacion.\n\n"
"El funcionamiento Bluetooth es 100% normal y se empareja directamente "
"con cualquier dispositivo (celular, tablet, laptop). Solo se pierde el "
"acceso a la app oficial de JBL.\n"
"==========================================\n\n"
"PRODUCTO REACONDICIONADO\n\n"
"Bocina JBL Charge 6 Bluetooth IP67 portatil, color negro. "
"Reacondicionada de fabrica: probada, limpia y certificada en "
"funcionamiento optimo. Puede presentar minimos detalles cosmeticos por "
"uso previo. Funcionamiento al 100%. Bateria recargable. Sonido potente. "
"Resistencia IP67 polvo y agua. Incluye cable de carga.\n\n"
"CARACTERISTICAS\n"
"- Conectividad: Bluetooth\n"
"- Resistencia: IP67 polvo y agua\n"
"- Bateria recargable de larga duracion\n"
"- App oficial JBL: NO COMPATIBLE\n"
"- Sonido potente\n"
"- Color: negro\n"
"- Estado: reacondicionado funcional\n\n"
"GARANTIA\n"
"30 dias del vendedor contra defectos de funcionamiento. NO aplica a: "
"incompatibilidad con app JBL (declarada en este aviso), preferencias "
"esteticas subjetivas.\n\n"
"Al comprar este articulo, el cliente acepta expresamente lo anterior."
)

attrs=[
  {"id":"BRAND","value_name":"JBL"},
  {"id":"MODEL","value_name":"Charge 6"},
  {"id":"WITH_BLUETOOTH","value_name":"Sí"},
  {"id":"IS_WATER_RESISTANT","value_name":"Sí"},
  {"id":"GTIN","value_name":"6925281987564"},
]

payload={
  "title": TITLE,
  "category_id": "MLM59800",
  "price": PRICE,
  "currency_id":"MXN",
  "available_quantity":1,
  "listing_type_id":"gold_special",
  "condition":"used",
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

p=requests.post(f"{API}/items",headers=HJA,json=payload,timeout=30)
print(f"\nPOST: {p.status_code}")
print(p.text[:2200])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJA,json={"plain_text":desc},timeout=20)
  print(f"\ndesc: {pd.status_code}")
  print(f"\n✅ CLONED {iid} @ ${d.get('price')} cond={d.get('condition')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
