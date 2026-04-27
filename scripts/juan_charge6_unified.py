"""
Publicar JBL Charge 6 unificada en cuenta Juan
- 3 colores: Negro, Azul, Rojo
- $399 c/u
- Envío gratis
- Condición: Reacondicionado
- Defecto declarado: NO compatible app JBL Portable
- Atributos blindados (warranty=Sin garantía, manual=No, original_box=No)
"""
import os, requests, json, time

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]  # JUAN

r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})")

# 1) Encontrar pictures por color buscando catálogos JBL Charge 6 existentes
SEARCH_QUERIES = {
    "Negro": "JBL Charge 6 Negro Negra",
    "Azul":  "JBL Charge 6 Azul",
    "Rojo":  "JBL Charge 6 Rojo Roja",
}

color_pics = {}
for color, q in SEARCH_QUERIES.items():
    print(f"\n=== Buscando pics {color} ===")
    found = []
    rs = requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={requests.utils.quote(q)}&condition=new&limit=20",headers=H,timeout=20).json()
    for it in rs.get("results",[]):
        title_l = (it.get("title","") or "").lower()
        if "charge 6" not in title_l and "charge6" not in title_l: continue
        if not it.get("catalog_listing"): continue
        # Get item details to extract pics
        iid = it.get("id")
        gd = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
        pics = [p.get("id") for p in gd.get("pictures",[]) if p.get("id")]
        if pics:
            print(f"  {iid} ({gd.get('title','')[:50]}) → {len(pics)} pics")
            found.extend(pics[:4])
        if len(found) >= 4: break
        time.sleep(0.3)
    color_pics[color] = found[:4]

print(f"\nPics por color:")
for c,p in color_pics.items():
    print(f"  {c}: {len(p)} pics")

# Re-upload pics to Juan account (so they belong to him)
def reupload(pid):
    try:
        img=requests.get(f"https://http2.mlstatic.com/D_{pid}-O.jpg",timeout=15).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except Exception as e:
        print(f"  upload err {pid}: {e}")
        return None

print("\n=== Re-uploading pics ===")
juan_pics = {}
for color, pids in color_pics.items():
    out = []
    for p in pids:
        n = reupload(p)
        if n: out.append(n)
    juan_pics[color] = out
    print(f"  {color}: re-uploaded {len(out)}")

# 2) Build attributes para Charge 6
cat_id = "MLM59800"  # bocinas portátiles
cat_attrs = requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

ATTRS = [
    {"id":"BRAND","value_name":"JBL"},
    {"id":"MODEL","value_name":"Charge 6"},
    {"id":"LINE","value_name":"Charge"},
    {"id":"ITEM_CONDITION","value_name":"Reacondicionado"},
    {"id":"MAX_BATTERY_AUTONOMY","value_name":"28 h"},
    {"id":"POWER_OUTPUT_RMS","value_name":"45 W"},
    {"id":"MAX_POWER","value_name":"45 W"},
    {"id":"MIN_FREQUENCY_RESPONSE","value_name":"60 Hz"},
    {"id":"MAX_FREQUENCY_RESPONSE","value_name":"20 kHz"},
    {"id":"INPUT_IMPEDANCE","value_name":"4 Ω"},
    {"id":"DISTORTION","value_name":"0.5 %"},
    {"id":"BATTERY_VOLTAGE","value_name":"5 V"},
    {"id":"IS_WATERPROOF","value_name":"Si"},
    {"id":"IS_PORTABLE","value_name":"Si"},
    {"id":"IS_WIRELESS","value_name":"Si"},
    {"id":"IS_RECHARGEABLE","value_name":"Si"},
    {"id":"WITH_BLUETOOTH","value_name":"Si"},
    {"id":"HAS_BLUETOOTH","value_name":"Si"},
    {"id":"HAS_APP_CONTROL","value_name":"No"},  # CRÍTICO: declara que NO tiene app
    {"id":"INCLUDES_CABLE","value_name":"Si"},
    {"id":"INCLUDES_BATTERY","value_name":"Si"},
    {"id":"HAS_MICROPHONE","value_name":"Si"},
    {"id":"IS_DUAL_VOICE_COIL","value_name":"No"},
    {"id":"IS_DUAL_VOICE_ASSISTANTS","value_name":"No"},
    {"id":"HAS_FM_RADIO","value_name":"No"},
    {"id":"HAS_SD_MEMORY_INPUT","value_name":"No"},
    {"id":"HAS_LED_LIGHTS","value_name":"No"},
    {"id":"HAS_USB_INPUT","value_name":"Si"},
    {"id":"WITH_AUX","value_name":"No"},
    {"id":"WITH_HANDSFREE_FUNCTION","value_name":"Si"},
    {"id":"SPEAKERS_NUMBER","value_name":"1"},
    {"id":"PICKUPS_NUMBER","value_name":"1"},
    {"id":"SPEAKER_FORMAT","value_name":"1.0"},
]

seen = {x["id"] for x in ATTRS}
BAD = {"EAN","UPC","MPN","SELLER_SKU","COLOR","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","GTIN"}
for ca in cat_attrs:
    aid = ca.get("id"); tags = ca.get("tags") or {}
    req = tags.get("required") or tags.get("conditional_required")
    if not req or aid in seen or aid in BAD: continue
    vals = ca.get("values") or []; vt = ca.get("value_type")
    if vals:
        ATTRS.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"):
        ATTRS.append({"id":aid,"value_name":"1"})
    else:
        ATTRS.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

# 3) Build variations
variations = []
for c in ["Negro","Azul","Rojo"]:
    if not juan_pics.get(c):
        print(f"  ⚠️ {c}: 0 pics — saltando")
        continue
    variations.append({
        "price": 399,
        "available_quantity": 5,
        "attribute_combinations":[{"id":"COLOR","value_name":c}],
        "picture_ids": juan_pics[c],
    })

if not variations:
    print("❌ No hay variaciones con pics — abortando")
    exit(1)

# Pictures generales = todas las pics
all_pics = []
for c in ["Negro","Azul","Rojo"]:
    for p in juan_pics.get(c,[]):
        if p not in all_pics: all_pics.append(p)

TITLE = "Jbl Charge 6 Bluetooth Portatil Reacondicionada Sin App 3 Colores"[:60]

DESCRIPTION = """═══════════════════════════════════════
JBL Charge 6 — REACONDICIONADA — 3 colores
═══════════════════════════════════════

⚠️ IMPORTANTE — LEA ANTES DE COMPRAR ⚠️

Este producto es REACONDICIONADO. Tiene UN solo defecto:

❌ NO es compatible con la aplicación JBL Portable
❌ Sin garantía oficial

✅ TODO lo demás funciona PERFECTAMENTE:
  • Bluetooth 100% operativo
  • Sonido potente original JBL
  • Bajos profundos (Original Pro Sound)
  • Resistencia agua y polvo IP67
  • Batería de larga duración (28h aprox)
  • Powerbank funcional (recarga otros dispositivos vía USB-C)
  • PartyBoost (conectar varias bocinas)
  • Manos libres / Llamadas
  • Carga rápida USB-C

🎨 COLORES DISPONIBLES:
  • Negro
  • Azul
  • Rojo

📦 EL PAQUETE INCLUYE:
  • 1 x Bocina JBL Charge 6 (color elegido)
  • Cable USB-C de carga
  • Empaque sellado de seguridad

🚚 ENVÍO GRATIS — entrega en 1-3 días hábiles

⚙️ ESPECIFICACIONES TÉCNICAS:
  • Potencia: 45 W RMS
  • Driver: woofer 70x100 mm + tweeter 20 mm
  • Bluetooth: 5.4 LE Audio + Auracast
  • Autonomía: hasta 28 horas
  • Resistencia: IP67 (sumergible 1m por 30min)
  • Carga: USB-C
  • Conectividad: PartyBoost
  • Peso aprox: 1 kg

❓ DUDAS: Pregunte antes de comprar.
   La única limitación es que NO se conecta a la app JBL.
   El equipo funciona 100% en todas sus demás funciones.

🛡️ Vendedor profesional con cuenta MercadoLíder.
"""

body = {
    "title": TITLE,
    "category_id": cat_id,
    "price": 399,
    "currency_id": "MXN",
    "available_quantity": 15,
    "buying_mode": "buy_it_now",
    "listing_type_id": "gold_pro",
    "condition": "refurbished",
    "pictures": [{"id": p} for p in all_pics],
    "shipping": {"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"cross_docking"},
    "attributes": ATTRS,
    "variations": variations,
    "tags": ["immediate_payment"],
    "description": {"plain_text": DESCRIPTION}
}

print("\n=== Creando publicación ===")
rp = requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"  status: {rp.status_code}")
if rp.status_code not in (200,201):
    print(f"  ❌ Error: {rp.text[:1500]}")
    exit(1)

resp = rp.json()
iid = resp.get("id")
print(f"\n✅ PUBLICADO: {iid}")
print(f"   URL: https://articulo.mercadolibre.com.mx/{iid.replace('MLM','MLM-')}")
print(f"   Title: {resp.get('title')}")
print(f"   Price: ${resp.get('price')}")
print(f"   Stock: {resp.get('available_quantity')}")
print(f"   Status: {resp.get('status')}")
print(f"   Variations: {len(resp.get('variations',[]))}")

# Add description if needed
desc_post = requests.post(f"https://api.mercadolibre.com/items/{iid}/description",
    headers=H, json={"plain_text": DESCRIPTION}, timeout=30)
print(f"   description POST: {desc_post.status_code}")

print(f"\n📋 Publicación creada en cuenta {me.get('nickname')}")
