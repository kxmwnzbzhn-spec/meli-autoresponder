import os, requests, json, time, base64
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
ITEM="MLM5510147104"

for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
r.raise_for_status(); tk=r.json(); AT=tk["access_token"]; NEW_RT=tk["refresh_token"]
print(f"[ROTATED] {NEW_RT}")
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# === NEW TITLE (58 chars, keyword Perfume first) ===
NEW_TITLE="Perfume Rabanne 1 Million Gold Elixir 100ml Hombre Original"
print(f"[new title] '{NEW_TITLE}' len={len(NEW_TITLE)}")

# === ATRIBUTOS SEO MELI MLM1271 ===
NEW_ATTRS=[
  {"id":"BRAND","value_name":"Rabanne"},
  {"id":"GTIN","value_name":"3349668644483"},
  {"id":"PERFUME_NAME","value_name":"1 Million Gold Elixir"},
  {"id":"LINE","value_name":"1 Million"},
  {"id":"MODEL","value_name":"1 Million Gold Elixir Parfum Intense"},
  {"id":"PERFUME_TYPE","value_name":"Parfum"},
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
]

# === PUT title + attributes ===
upd=requests.put(f"{API}/items/{ITEM}",headers=H,
  json={"title":NEW_TITLE,"attributes":NEW_ATTRS},timeout=20)
print(f"[PUT title+attrs] HTTP {upd.status_code}")
if upd.status_code>=300:
  print(f"  body: {upd.text[:1200]}")

# === SEO DESCRIPTION ===
# Primeros 200 chars = lo que MELI muestra en snippets de búsqueda. Saturados de keywords.
DESC="""Perfume Rabanne 1 Million Gold Elixir Parfum Intense 100 ml Hombre - 100% Original Sellado en Caja - Envío Inmediato - Garantía del Vendedor.

🥇 LO MÁS IMPORTANTE PRIMERO
• Producto 100% original importado, sellado en caja de fábrica.
• Presentación: spray atomizador de 100 ml.
• Para hombre - fragancia masculina premium.
• Concentración: Parfum Intense (más duradera que un EDP estándar).
• Envío inmediato el mismo día o siguiente día hábil.

🌟 SOBRE LA FRAGANCIA - 1 MILLION GOLD ELIXIR
Una reinterpretación dorada e intensa del icónico 1 Million. Más profunda, más sensual, más larga en piel. Pensada para el hombre que quiere imponer presencia desde el primer instante.

🌿 PIRÁMIDE OLFATIVA
• Notas de Salida: Bergamota italiana y Cardamomo verde - apertura cítrica y especiada.
• Notas de Corazón: Canela y Cuero - acorde cálido y seductor.
• Notas de Fondo: Ámbar dorado, Maderas preciosas y Vainilla - drydown profundo y persistente.

⏱ DURACIÓN Y PROYECCIÓN
• Duración en piel: 10 a 12 horas.
• Proyección: alta durante las primeras 4 horas, moderada después.
• Estela perceptible a 1-2 metros en su pico.

🎯 ¿PARA QUIÉN ES?
• Hombre que busca un perfume seductor para la noche y ocasiones especiales.
• Ideal para citas, eventos formales, salidas nocturnas, oficina ejecutiva.
• Edad sugerida: 25 años en adelante.
• Estación recomendada: otoño-invierno (también funciona en climas fríos de primavera).

🎁 LO QUE RECIBES
• 1 frasco spray Rabanne 1 Million Gold Elixir Parfum Intense de 100 ml.
• Caja original de Rabanne con código de barras y holograma de autenticidad.
• Producto sellado, sin abrir, sin probar.

✅ GARANTÍAS QUE TE DAMOS
• Producto 100% Original o te devolvemos tu dinero.
• Garantía del vendedor: 30 días por cualquier defecto de fábrica.
• Si tienes dudas, escríbenos por mensajes de Mercado Libre antes de comprar.

📦 ENVÍO
• Empaquetado profesional con material protector adicional.
• Envío el mismo día si compras antes de las 14:00 hrs.
• Te enviamos el número de guía en cuanto el paquete sale.

🔍 BÚSQUEDAS RELACIONADAS
Perfume Rabanne, Paco Rabanne, 1 Million, One Million, Million Gold, Gold Elixir Parfum, Million Parfum Intense, perfume hombre 100ml, loción Rabanne, fragancia masculina dorada, perfume hombre original, perfume largo duración, perfume hombre seductor, Rabanne hombre, perfume de noche hombre.

❓ PREGUNTAS FRECUENTES
P: ¿Es original?
R: Sí, 100% original importado de España. Caja sellada con holograma Rabanne.

P: ¿Cuánto dura en piel?
R: Entre 10 y 12 horas en piel normal. Mejor proyección sobre piel limpia e hidratada.

P: ¿Es diferente al 1 Million normal?
R: Sí, el Gold Elixir es la versión Parfum Intense - más concentrado, más duradero, con notas amaderadas y dulces más marcadas que el EDT clásico.

P: ¿Llega con factura?
R: Sí, generamos factura automática cuando compras."""

# Try multiple combos to find what this listing accepts
import html as _h
DESC_HTML="<p>"+_h.escape(DESC).replace("\n\n","</p><p>").replace("\n","<br>")+"</p>"
print("--- try 1: ONLY text(html) ---")
rd=requests.put(f"{API}/items/{ITEM}/description",headers=H,
  json={"text":DESC_HTML},timeout=15)
print(f"  HTTP {rd.status_code}: {rd.text[:300]}")
if rd.status_code>=300:
  print("--- try 2: DELETE + POST plain_text ---")
  d=requests.delete(f"{API}/items/{ITEM}/description",headers=H,timeout=15)
  print(f"  DELETE HTTP {d.status_code}")
  rd=requests.post(f"{API}/items/{ITEM}/description",headers=H,
    json={"plain_text":DESC},timeout=15)
  print(f"  POST plain HTTP {rd.status_code}: {rd.text[:300]}")
  if rd.status_code>=300:
    print("--- try 3: POST text(html) ---")
    rd=requests.post(f"{API}/items/{ITEM}/description",headers=H,
      json={"text":DESC_HTML},timeout=15)
    print(f"  POST html HTTP {rd.status_code}: {rd.text[:300]}")
print(f"[PUT description] HTTP {rd.status_code} - {len(DESC)} chars\n  body: {rd.text[:400]}")

# Verify
g=requests.get(f"{API}/items/{ITEM}",headers={"Authorization":f"Bearer {AT}"},timeout=15).json()
print(f"\n[VERIFY] title: {g.get('title')}")
print(f"  price={g.get('price')} qty={g.get('available_quantity')} status={g.get('status')}")
print(f"  attribute count: {len(g.get('attributes',[]))}")

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
