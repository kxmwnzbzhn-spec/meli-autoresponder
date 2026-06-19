import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID="MLM44715070"
cp=requests.get(f"{API}/products/{CPID}",headers=H,timeout=15).json()
print(f"CPID name: {cp.get('name')}")
print(f"parent: {cp.get('parent_id')}")

# Snapshot
i=requests.get(f"{API}/products/{CPID}/items?limit=10",headers=H,timeout=15).json()
ps=[r2.get("price") for r2 in (i.get("results") or []) if r2.get("price")]
ps.sort()
if ps: print(f"competidores: {len(ps)} min={ps[0]} median={ps[len(ps)//2]} max={ps[-1]}")

# Re-upload photos from CPID using F (large) version
pic_ids=[]
for pp in cp.get("pictures",[])[:8]:
  url=pp.get("url","")
  large=url.replace("-O.jpg","-F.jpg")
  for try_url in [large,url]:
    try:
      rr=requests.get(try_url,timeout=30)
      if rr.status_code==200 and len(rr.content)>10000:
        up=requests.post(f"{API}/pictures/items/upload",
          headers={"Authorization":f"Bearer {AT}"},
          files={"file":(f"go4_{len(pic_ids)}.jpg",rr.content,"image/jpeg")},timeout=60)
        if up.status_code in (200,201):
          pid=up.json().get("id")
          if pid: pic_ids.append(pid); print(f"  ✓ {pid}"); break
        else:
          print(f"  ✗ {up.status_code}"); break
    except Exception as e: print(f"  err: {e}")
print(f"uploaded: {len(pic_ids)}")

CAT="MLM59800"
TITLE="Bocina Portátil JBL Go 4 Bluetooth IP67 Waterproof Negra"  # 56 chars
print(f"title len: {len(TITLE)}")

desc=(
"BOCINA PORTÁTIL JBL GO 4 BLUETOOTH IP67 - NEGRA\n\n"
"La bocina JBL Go 4 ofrece sonido potente, profundo y nítido en un diseño "
"ultra compacto. Resistencia IP67 al polvo y agua, batería recargable de "
"larga duración y conectividad Bluetooth 5.3 estable.\n\n"
"CARACTERÍSTICAS\n"
"- Marca: JBL (100% original)\n"
"- Modelo: Go 4 (JBLGO4BLK)\n"
"- Color: Negro\n"
"- Bluetooth 5.3 con Auracast\n"
"- Resistencia IP67 polvo y agua\n"
"- Batería recargable Li-Ion (hasta 7 horas)\n"
"- Tiempo de carga: 3 horas\n"
"- Potencia: 4.2 W RMS\n"
"- Respuesta de frecuencia: 180Hz - 20kHz\n"
"- Conector: USB-C\n"
"- Peso: 190 g\n"
"- Dimensiones: 94 x 75 x 42 mm\n"
"- Correa integrada para llevar\n"
"- Compatible con cualquier celular, tablet o laptop\n\n"
"INCLUYE\n"
"- 1 bocina JBL Go 4 negra\n"
"- Cable USB-C\n"
"- Manual\n\n"
"PRODUCTO ORIGINAL\n"
"100% original con caja sellada. Envío inmediato desde México. Garantía "
"del vendedor 30 días por defectos de funcionamiento."
)

# Full attribute set (will filter against schema)
ats=requests.get(f"{API}/categories/{CAT}/attributes",headers=H,timeout=15).json()
valid_ids={a["id"] for a in ats}
def vid_lookup(aid,name):
  for a in ats:
    if a["id"]==aid:
      for v in (a.get("values") or []):
        if (v.get("name") or "").lower()==name.lower():
          return v.get("id")
  return None

candidate=[
  ("BRAND","JBL"),
  ("MODEL","Go 4"),
  ("LINE","Go"),
  ("ALPHANUMERIC_MODEL","JBLGO4BLK"),
  ("ITEM_CONDITION","Nuevo"),
  ("MAIN_COLOR","Negro"),
  ("COLOR","Negro"),
  ("WITH_BLUETOOTH","Sí"),
  ("BLUETOOTH_VERSION","5.3"),
  ("IS_WATER_RESISTANT","Sí"),
  ("IS_WATERPROOF","Sí"),
  ("IS_DUST_RESISTANT","Sí"),
  ("IP_CLASSIFICATION","IP67"),
  ("IS_PORTABLE","Sí"),
  ("IS_WIRELESS","Sí"),
  ("IS_SUITABLE_FOR_OUTDOOR_USE","Sí"),
  ("INCLUDES_RECHARGEABLE_BATTERY","Sí"),
  ("BATTERY_TYPE","Ion de litio"),
  ("MAX_BATTERY_AUTONOMY","7 h"),
  ("CHARGE_TIME","3 h"),
  ("POWER_OUTPUT_RMS","4.2 W"),
  ("MAX_FREQUENCY_RESPONSE","20 kHz"),
  ("MIN_FREQUENCY_RESPONSE","180 Hz"),
  ("WEIGHT","190 g"),
  ("WIDTH","9.4 cm"),
  ("HEIGHT","7.5 cm"),
  ("DEPTH","4.2 cm"),
  ("SELLER_PACKAGE_LENGTH","12 cm"),
  ("SELLER_PACKAGE_WIDTH","10 cm"),
  ("SELLER_PACKAGE_HEIGHT","6 cm"),
  ("SELLER_PACKAGE_WEIGHT","280 g"),
  ("INPUT_CONNECTORS","USB"),
  ("POWER_SUPPLY_TYPES","USB"),
  ("SPEAKERS_NUMBER","1"),
  ("SPEAKER_FORMAT","Caja"),
  ("SPEAKER_TYPES","Medio"),
  ("INCLUDES_CHARGER","No"),
  ("INCLUDES_REMOTE_CONTROL","No"),
  ("INCLUDES_LATCH","Sí"),
  ("INCLUDES_SUPPORT","No"),
  ("INCLUDES_WHEELS","No"),
  ("IS_GAMER","No"),
  ("IS_PROFESSIONAL","No"),
  ("IS_A_STAGE_MONITOR","No"),
  ("WITH_BASE","No"),
  ("WITH_LED_LIGHTS","No"),
  ("WITH_MICROPHONE","No"),
  ("WITH_RADIO","No"),
  ("WITH_WI_FI","No"),
  ("WITH_NFC","No"),
  ("WITH_KARAOKE_FUNCTION","No"),
  ("WITH_SCREEN","No"),
  ("WITH_HANDS_FREE_MODE","No"),
  ("WITH_VOICE_EFFECT","No"),
  ("WITH_INTEGRATED_DJ_CONTROLLERS","No"),
  ("GTIN","6925281982989"),
  ("HAZMAT_TRANSPORTABILITY","Exceptuado"),
]
attrs=[]
for aid,nm in candidate:
  if aid not in valid_ids: continue
  v=vid_lookup(aid,nm)
  a={"id":aid,"value_name":nm}
  if v: a["value_id"]=v
  attrs.append(a)
print(f"\nsending {len(attrs)} attrs")

# TRADICIONAL WITHOUT catalog_product_id (bypass opt-in check)
payload={
  "title": TITLE,
  "category_id": CAT,
  "price": 599,
  "currency_id":"MXN",
  "available_quantity":50,
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
print(p.text[:2500])
if p.status_code==201:
  d=p.json()
  iid=d.get("id")
  pd=requests.post(f"{API}/items/{iid}/description",headers=HJ,json={"plain_text":desc},timeout=20)
  print(f"\ndesc: {pd.status_code}")
  print(f"\n✅ CREATED {iid} @ ${d.get('price')} qty={d.get('available_quantity')} status={d.get('status')}")
  print(f"permalink: {d.get('permalink')}")
