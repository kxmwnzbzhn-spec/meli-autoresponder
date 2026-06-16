import os, requests, json, time, base64, sys, html as _h
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(5):
  r=requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(6)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

DRIVE_IDS=[
  "13CtzU4L6K20jGMHighOIKt6SMetzaMMr","19lcNzvoAENSrrhXjx0a_5HfRmyws1lyG",
  "1BJybdmw8wMYYPPZZaHcFCfYdPWHCRz4r","1DzouYTNguG3hbuwl4-tn98Ui_2XpGdFf",
  "1HoJu5ALifJVxckog4_j-Krc6emYsVg2c","1Ht4rmwHMcg14G5FXvAzZ9kYVRqvLM5vG",
  "1K0TZJRQLfPzi4O6PohTgFEdjAt7KAbxb","1Y13QPytceA5f-8ijrUR387gFWZ1kccEE",
  "1bESZDVulLeSGInaWR9KUZy25D-5I2V2K","1bk4tPECiPlBjptB4WARdDYbozepRB5kR",
  "1hF8Y47n2AQqnBLxr4WGgM-TC5VkvfJ-b","1naV7YH0ET07q8V2iyX248LdV8uIhL9kG",
  "1qtEnLxcGW3H6csBQ0wJL285SuTEDLTV0","1ytoBaShUp7dkEpn59ej3dqvg9fshmfQy",
]

uploaded=[]
for i,FID in enumerate(DRIVE_IDS,1):
  # Try MELI's source-URL fetch first (lh3 endpoint is reliable)
  url=f"https://lh3.googleusercontent.com/d/{FID}=w2048"
  try:
    img=requests.get(url,timeout=25)
    ct=img.headers.get("content-type","")
    if img.status_code!=200 or not ct.startswith("image/") or len(img.content)<2000:
      # fallback to uc?export=download
      url2=f"https://drive.google.com/uc?export=download&id={FID}"
      img=requests.get(url2,timeout=25,allow_redirects=True)
    print(f"[{i}/14] {FID[:8]}... downloaded {len(img.content)} bytes ({img.headers.get('content-type','?')})")
    if len(img.content)<2000:
      print(f"  ⚠️ too small, skip"); continue
    # Upload to MELI
    files={'file':(f'photo_{i}.jpg',img.content,'image/jpeg')}
    up=requests.post("https://api.mercadolibre.com/pictures/items/upload",
      headers={"Authorization":f"Bearer {AT}"},files=files,timeout=30)
    print(f"  upload HTTP {up.status_code}")
    if up.status_code<300:
      pid=up.json().get("id")
      print(f"  ✅ MELI picture id: {pid}")
      uploaded.append(pid)
    else:
      print(f"  ❌ {up.text[:200]}")
  except Exception as e:
    print(f"  ERR {e}")

print(f"\n=== {len(uploaded)} fotos subidas a MELI ===")
if not uploaded:
  print("ABORT: 0 fotos OK"); sys.exit(1)

# Build pictures with id refs
pictures=[{"id":p} for p in uploaded[:10]]

TITLE="Perfume Jo Milano Game Of Spades Wildcard 100ml Hombre EDP"
body={
  "title":TITLE,
  "category_id":"MLM1271",
  "price":1499,
  "currency_id":"MXN",
  "available_quantity":1,
  "buying_mode":"buy_it_now",
  "condition":"new",
  "listing_type_id":"gold_special",
  "pictures":pictures,
  "attributes":[
    {"id":"BRAND","value_name":"Jo Milano"},
    {"id":"LINE","value_name":"Game of Spades"},
    {"id":"PERFUME_NAME","value_name":"Wildcard"},
    {"id":"MODEL","value_name":"Game of Spades Wildcard"},
    {"id":"PERFUME_TYPE","value_name":"Eau de parfum"},
    {"id":"UNIT_VOLUME","value_name":"100 mL"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"},
    {"id":"FRAGRANCE_FAMILY","value_name":"Oriental amaderado"},
    {"id":"SCENT_INTENSITY","value_name":"Intenso"},
    {"id":"APPLICATION_AREA","value_name":"Cuerpo"},
    {"id":"AGE_GROUP","value_name":"Adultos"},
    {"id":"PACKAGING_TYPE","value_name":"Spray"},
    {"id":"UNITS_PER_PACK","value_name":"1"},
    {"id":"SCENT_NOTES","value_name":"Bergamota, Pimienta negra, Cuero, Tabaco, Ámbar, Maderas oscuras, Vainilla"},
    {"id":"COUNTRY_OF_ORIGIN","value_name":"Estados Unidos"},
    {"id":"WITH_EXPIRATION_DATE","value_name":"No"},
    {"id":"GTIN","value_name":"0860005113040"},
  ],
}

v=requests.post("https://api.mercadolibre.com/items/validate",headers=H,json=body,timeout=20)
print(f"[VALIDATE] HTTP {v.status_code}")
if v.status_code>=300:
  try:
    j=v.json(); causes=j.get("cause",[])
    err=[c for c in causes if c.get("type")=="error"]
    if err: print(f"  ERR: {json.dumps(err,ensure_ascii=False)[:600]}")
  except: print(v.text[:500])

p=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
print(f"[POST] HTTP {p.status_code}")
if p.status_code>=300:
  print(p.text[:1000]); sys.exit(1)
out=p.json(); NEW_ID=out["id"]
print(f"✅ {NEW_ID} ${body['price']} | https://articulo.mercadolibre.com.mx/{NEW_ID.replace('MLM','MLM-')}-_JM")

DESC=("""Perfume Jo Milano Game Of Spades Wildcard 100 ml Hombre Eau de Parfum - 100% Original Importado - Envío Inmediato - Garantía del Vendedor.

🥇 LO MÁS IMPORTANTE PRIMERO
• Producto 100% original importado de Estados Unidos.
• Presentación: spray atomizador de 100 ml.
• Para hombre - fragancia masculina premium oriental amaderada.
• Concentración: Eau de Parfum (EDP) - alta longevidad.
• Envío inmediato el mismo día o siguiente día hábil.

🌟 SOBRE LA FRAGANCIA - GAME OF SPADES WILDCARD
Edición Wildcard de la línea Game of Spades de Jo Milano. Una fragancia poderosa, misteriosa y seductora, pensada para el hombre que rompe las reglas y juega su propia partida. Estela intensa, drydown profundo y carácter dominante desde la primera nota.

🌿 PIRÁMIDE OLFATIVA
• Notas de Salida: Bergamota italiana, Pimienta negra - apertura especiada y picante.
• Notas de Corazón: Cuero, Tabaco - acorde masculino oscuro y carismático.
• Notas de Fondo: Ámbar dorado, Maderas oscuras, Vainilla - drydown adictivo y persistente.

⏱ DURACIÓN Y PROYECCIÓN
• Duración en piel: 8 a 12 horas.
• Proyección: alta durante las primeras 4 horas, moderada después.
• Estela perceptible a 1.5-2 metros en su pico inicial.

🎯 ¿PARA QUIÉN ES?
• Hombre que busca un perfume con carácter para noche, citas y ocasiones especiales.
• Ideal para eventos formales, salidas nocturnas, cenas, oficina ejecutiva.
• Edad sugerida: 25 años en adelante.
• Estación recomendada: otoño-invierno.

🎁 LO QUE RECIBES
• 1 frasco spray Jo Milano Game Of Spades Wildcard EDP de 100 ml.
• Caja original Jo Milano con sello y datos de autenticidad.
• Producto sellado, sin abrir, sin probar.

✅ GARANTÍAS QUE TE DAMOS
• Producto 100% Original o te devolvemos tu dinero.
• Garantía del vendedor: 30 días por cualquier defecto de fábrica.

📦 ENVÍO
• Empaquetado profesional con material protector adicional.
• Envío el mismo día si compras antes de las 14:00 hrs.
• Te enviamos el número de guía cuando el paquete sale.

🔍 BÚSQUEDAS RELACIONADAS
Perfume Jo Milano, Game Of Spades, Wildcard, Jo Milano Wildcard EDP, perfume hombre 100ml, loción Jo Milano, perfume nicho hombre, perfume largo duración, perfume hombre original, fragancia masculina oriental, perfume hombre seductor.

❓ PREGUNTAS FRECUENTES
P: ¿Es original?
R: Sí, 100% original importado. Caja sellada.

P: ¿Cuánto dura en piel?
R: Entre 8 y 12 horas en piel normal.

P: ¿Qué tipo de fragancia es?
R: Oriental amaderado con acordes de cuero y tabaco. Ideal para noche.

P: ¿Llega con factura?
R: Sí.""")

DESC_HTML="<p>"+_h.escape(DESC).replace("\n\n","</p><p>").replace("\n","<br>")+"</p>"
rd=requests.put(f"https://api.mercadolibre.com/items/{NEW_ID}/description",
  headers=H,json={"text":DESC_HTML},timeout=15)
print(f"[desc] HTTP {rd.status_code}")

# Sync RT
try: import nacl.encoding, nacl.public
except: os.system("pip install pynacl -q"); import nacl.encoding, nacl.public
GHT=os.environ.get("GH_PAT")
if GHT and NEW_RT:
  GHH={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"}
  R="kxmwnzbzhn-spec/meli-autoresponder"
  pk=requests.get(f"https://api.github.com/repos/{R}/actions/secrets/public-key",headers=GHH,timeout=15).json()
  pub=nacl.public.PublicKey(base64.b64decode(pk["key"]))
  sealed=nacl.public.SealedBox(pub).encrypt(NEW_RT.encode())
  enc=base64.b64encode(sealed).decode()
  requests.put(f"https://api.github.com/repos/{R}/actions/secrets/MELI_REFRESH_TOKEN_AH",
    headers=GHH,json={"encrypted_value":enc,"key_id":pk["key_id"]},timeout=15)
