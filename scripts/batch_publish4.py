import os, requests, json, sys, time, base64
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]

for a in range(5):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(6)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

def get_pics_from_src(src_item):
  g=requests.get(f"{API}/items/{src_item}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
  return [{"source":p["secure_url"]} for p in (g.get("pictures") or [])][:10]

def get_pics_from_cpid(cpid):
  cp=requests.get(f"{API}/products/{cpid}",headers={"Authorization":f"Bearer {AT}"},timeout=12).json()
  return [{"source":p["url"]} for p in (cp.get("pictures") or [])][:10]

def publish(label, body):
  v=requests.post(f"{API}/items/validate",headers=H,json=body,timeout=20)
  print(f"\n=== {label} ===")
  print(f"[VALIDATE] HTTP {v.status_code}")
  if v.status_code>=300:
    try:
      j=v.json(); err=[c for c in j.get("cause",[]) if c.get("type")=="error"]
      if err: print(f"  ERR: {json.dumps(err,ensure_ascii=False)[:1000]}"); return None
    except: pass
  p=requests.post(f"{API}/items",headers=H,json=body,timeout=25)
  print(f"[POST] HTTP {p.status_code}")
  if p.status_code>=300: print(f"  body: {p.text[:800]}"); return None
  out=p.json()
  print(f"  ✅ {out['id']} ${body['price']} | https://articulo.mercadolibre.com.mx/{out['id'].replace('MLM','MLM-')}-_JM")
  return out

# === ITEM 1: Armaf Club De Nuit Iconic 105ml — clone tradicional $499 ===
pics1=get_pics_from_src("MLM2969825393")
body1={
  "title":"Perfume Armaf Club de Nuit Iconic Eau de Parfum 105ml Hombre",
  "category_id":"MLM1271","price":499,"currency_id":"MXN",
  "available_quantity":1,"buying_mode":"buy_it_now","condition":"new",
  "listing_type_id":"gold_special","pictures":pics1,
  "attributes":[
    {"id":"BRAND","value_name":"Armaf"},
    {"id":"GTIN","value_name":"6294015164497"},
    {"id":"PERFUME_NAME","value_name":"Club de Nuit Iconic"},
    {"id":"PERFUME_TYPE","value_name":"Eau de parfum"},
    {"id":"UNIT_VOLUME","value_name":"105 mL"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"},
    {"id":"MODEL","value_name":"Club de Nuit Iconic"},
    {"id":"LINE","value_name":"Club de Nuit"},
  ]}
out1=publish("ARMAF ICONIC 105ml @ $499", body1)

# === ITEM 2: Luxury Collection Royal Amber 80ml — clone tradicional $699 ===
pics2=get_pics_from_src("MLM2969827221")
body2={
  "title":"Perfume Luxury Collection Royal Amber 80ml Unisex Importado",
  "category_id":"MLM1271","price":699,"currency_id":"MXN",
  "available_quantity":1,"buying_mode":"buy_it_now","condition":"new",
  "listing_type_id":"gold_special","pictures":pics2,
  "attributes":[
    {"id":"BRAND","value_name":"Luxury Collection"},
    {"id":"PERFUME_NAME","value_name":"Royal Amber"},
    {"id":"PERFUME_TYPE","value_name":"Eau de parfum"},
    {"id":"UNIT_VOLUME","value_name":"80 mL"},
    {"id":"GENDER","value_name":"Sin género"},
    {"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"},
    {"id":"MODEL","value_name":"Royal Amber"},
    {"id":"EMPTY_GTIN_REASON","value_name":"El producto no tiene código registrado"},
  ]}
out2=publish("LUXURY ROYAL AMBER 80ml @ $699", body2)

# === ITEM 3: Armaf The Lions Club Rugir 100ml — clone tradicional $799 ===
pics3=get_pics_from_src("MLM2969825239")
body3={
  "title":"Perfume Armaf The Lions Club Rugir 100ml EDP Hombre Original",
  "category_id":"MLM1271","price":799,"currency_id":"MXN",
  "available_quantity":1,"buying_mode":"buy_it_now","condition":"new",
  "listing_type_id":"gold_special","pictures":pics3,
  "attributes":[
    {"id":"BRAND","value_name":"Armaf"},
    {"id":"PERFUME_NAME","value_name":"The Lions Club Rugir"},
    {"id":"PERFUME_TYPE","value_name":"Eau de parfum"},
    {"id":"UNIT_VOLUME","value_name":"100 mL"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"ITEM_CONDITION","value_id":"2230284","value_name":"Nuevo"},
    {"id":"MODEL","value_name":"The Lions Club Rugir"},
    {"id":"LINE","value_name":"The Lions Club"},
    {"id":"GTIN","value_name":"6294015100013"},
  ]}
out3=publish("ARMAF LIONS RUGIR 100ml @ $799", body3)

# === ITEM 4: Rabanne 1 Million Gold EDP 100ml — SEO-optimized tradicional ===
# CPID MLM39361112 — competitors: $1765 - $2860. Safe floor: $1599
pics4=get_pics_from_cpid("MLM39361112")
TITLE4="Perfume Rabanne 1 Million Gold EDP 100ml Hombre Original Sellado"
print(f"\n[title4 len] {len(TITLE4)}")
body4={
  "title":TITLE4,
  "category_id":"MLM1271","price":1599,"currency_id":"MXN",
  "available_quantity":1,"buying_mode":"buy_it_now","condition":"new",
  "listing_type_id":"gold_special","pictures":pics4,
  "attributes":[
    {"id":"BRAND","value_name":"Rabanne"},
    {"id":"GTIN","value_name":"3349668629398"},
    {"id":"PERFUME_NAME","value_name":"1 Million Gold"},
    {"id":"LINE","value_name":"1 Million"},
    {"id":"MODEL","value_name":"1 Million Gold Eau de Parfum"},
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
    {"id":"SCENT_NOTES","value_name":"Bergamota, Cardamomo, Canela, Cuero, Ámbar, Vainilla, Maderas"},
    {"id":"COUNTRY_OF_ORIGIN","value_name":"España"},
    {"id":"WITH_EXPIRATION_DATE","value_name":"No"},
  ]}
out4=publish("RABANNE MILLION GOLD EDP 100ml @ $1599", body4)

# === Description SEO para item 4 ===
if out4:
  DESC=("""Perfume Rabanne 1 Million Gold Eau de Parfum 100 ml Hombre - 100% Original Sellado en Caja - Envío Inmediato - Garantía del Vendedor.

🥇 LO MÁS IMPORTANTE PRIMERO
• Producto 100% original importado, sellado en caja de fábrica.
• Presentación: spray atomizador de 100 ml.
• Para hombre - fragancia masculina premium.
• Concentración: Eau de Parfum (EDP).
• Envío inmediato el mismo día o siguiente día hábil.

🌟 SOBRE LA FRAGANCIA - 1 MILLION GOLD
La versión dorada del icónico 1 Million de Rabanne. Más cálido, más sensual, con un acorde ámbar y maderas que envuelve. Para el hombre que quiere imponer presencia desde el primer instante.

🌿 PIRÁMIDE OLFATIVA
• Notas de Salida: Bergamota italiana, Cardamomo - apertura cítrica y especiada.
• Notas de Corazón: Canela, Cuero - acorde cálido seductor.
• Notas de Fondo: Ámbar, Maderas preciosas, Vainilla - drydown profundo persistente.

⏱ DURACIÓN Y PROYECCIÓN
• Duración en piel: 8 a 10 horas.
• Proyección: alta primeras 3 horas, moderada después.
• Estela perceptible a 1-2 metros.

🎯 ¿PARA QUIÉN ES?
• Hombre que busca un perfume seductor para noche y ocasiones especiales.
• Ideal para citas, eventos formales, salidas nocturnas, oficina ejecutiva.
• Edad sugerida: 25 años en adelante.
• Estación recomendada: otoño-invierno.

🎁 LO QUE RECIBES
• 1 frasco spray Rabanne 1 Million Gold EDP de 100 ml.
• Caja original de Rabanne con código de barras y holograma.
• Producto sellado, sin abrir.

✅ GARANTÍAS
• Producto 100% Original o te devolvemos tu dinero.
• Garantía del vendedor: 30 días por defectos de fábrica.
• Cualquier duda escríbenos por mensajes de Mercado Libre antes de comprar.

📦 ENVÍO
• Empaquetado profesional con material protector.
• Envío el mismo día si compras antes de las 14:00 hrs.
• Te enviamos el número de guía cuando el paquete sale.

🔍 BÚSQUEDAS RELACIONADAS
Perfume Rabanne, Paco Rabanne, 1 Million, One Million, Million Gold, Gold EDP, perfume hombre 100ml, loción Rabanne, fragancia masculina, perfume hombre original, perfume largo duración, perfume hombre seductor, Rabanne hombre, perfume oriental amaderado.

❓ PREGUNTAS FRECUENTES
P: ¿Es original?
R: Sí, 100% original importado de España. Caja sellada con holograma Rabanne.

P: ¿Cuánto dura en piel?
R: Entre 8 y 10 horas en piel normal. Mejor proyección sobre piel limpia e hidratada.

P: ¿Es diferente al 1 Million normal?
R: Sí, la versión Gold tiene un perfil más cálido, dulce y amaderado vs el original.

P: ¿Llega con factura?
R: Sí, generamos factura automática.""")
  import html as _h
  DESC_HTML="<p>"+_h.escape(DESC).replace("\n\n","</p><p>").replace("\n","<br>")+"</p>"
  rd=requests.put(f"{API}/items/{out4['id']}/description",headers=H,json={"text":DESC_HTML},timeout=15)
  print(f"\n[desc PUT for {out4['id']}] HTTP {rd.status_code}")
  # Setup priority replenish for Million Gold EDP
  SB=os.environ["SUPABASE_URL"].rstrip("/"); SBK=os.environ["SUPABASE_SERVICE_KEY"]
  SBH={"apikey":SBK,"Authorization":f"Bearer {SBK}","Content-Type":"application/json",
       "Prefer":"return=representation,resolution=merge-duplicates"}
  rp=requests.post(f"{SB}/rest/v1/meli_priority_replenish",headers=SBH,
    json={"item_id":out4['id'],"account":"AH","default_qty":1,"product_name":TITLE4},timeout=12)
  print(f"[priority_replenish for {out4['id']}] HTTP {rp.status_code}")

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
  print("[RT sync] done")
