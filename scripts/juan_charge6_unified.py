"""
Publicar JBL Charge 6 unificada en cuenta Juan
- 3 colores: Negro, Azul, Rojo
- $399 c/u, envío gratis, condición Reacondicionado
"""
import os, requests, json, time

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]

r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})")

def search_catalog_urls(query):
    rs = requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={requests.utils.quote(query)}&limit=5",headers=H,timeout=20).json()
    print(f"  catalog '{query}' resultados: {len(rs.get('results',[]))}")
    urls = []
    for p in rs.get("results", [])[:3]:
        pid = p.get("id")
        if not pid: continue
        prod = requests.get(f"https://api.mercadolibre.com/products/{pid}",headers=H,timeout=10).json()
        for pic in (prod.get("pictures") or [])[:5]:
            url = pic.get("url","")
            if url and url.startswith("http"):
                urls.append(url)
        if urls: break
    return urls[:5]

def search_listing_urls(query):
    rs = requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={requests.utils.quote(query)}&limit=15",headers=H,timeout=20).json()
    urls = []
    for it in rs.get("results", []):
        title_l = (it.get("title","") or "").lower()
        if "charge" not in title_l: continue
        iid = it.get("id")
        gd = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
        for p in (gd.get("pictures") or [])[:5]:
            u = p.get("url","")
            if u and u.startswith("http"): urls.append(u)
        if len(urls) >= 4: break
        time.sleep(0.2)
    return urls[:5]

color_urls = {}
for color, q in [("Negro","Jbl Charge 6 Negra"), ("Azul","Jbl Charge 6 Azul"), ("Rojo","Jbl Charge 6 Roja")]:
    print(f"\n=== {color} ===")
    urls = search_catalog_urls(q)
    if not urls:
        urls = search_listing_urls(q)
    color_urls[color] = urls
    print(f"  URLs: {len(urls)}")
    for u in urls[:2]: print(f"    {u}")

def upload_url(url):
    """Download by URL and upload."""
    try:
        img = requests.get(url, timeout=20).content
        if len(img) < 2000:
            print(f"    img too small: {len(img)}b")
            return None
        rp = requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        if rp.status_code in (200,201):
            return rp.json().get("id")
        else:
            print(f"    upload err HTTP {rp.status_code}: {rp.text[:200]}")
            return None
    except Exception as e:
        print(f"    err: {e}")
        return None

print("\n=== Re-uploading ===")
juan_pics = {}
for color, urls in color_urls.items():
    out = []
    for u in urls:
        pid = upload_url(u)
        if pid: out.append(pid)
        time.sleep(0.3)
    juan_pics[color] = out
    print(f"  {color}: {len(out)}/{len(urls)} re-uploaded")

total_pics = sum(len(v) for v in juan_pics.values())
if total_pics == 0:
    print("\n❌ NO HAY PICS — abortando")
    exit(1)

cat_id = "MLM59800"
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
    {"id":"HAS_APP_CONTROL","value_name":"No"},
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

variations = []
for c in ["Negro","Azul","Rojo"]:
    if not juan_pics.get(c):
        for fb in ["Negro","Azul","Rojo"]:
            if juan_pics.get(fb):
                juan_pics[c] = juan_pics[fb][:2]
                print(f"  {c} fallback usando {fb}")
                break
    if not juan_pics.get(c): continue
    variations.append({
        "price": 399,
        "available_quantity": 5,
        "attribute_combinations":[{"id":"COLOR","value_name":c}],
        "picture_ids": juan_pics[c],
    })

if not variations:
    print("❌ Sin variaciones"); exit(1)

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
  • Bajos profundos
  • Resistencia agua y polvo IP67
  • Batería de larga duración (28h aprox)
  • Powerbank funcional (USB-C)
  • PartyBoost
  • Manos libres
  • Carga rápida USB-C

🎨 COLORES: Negro, Azul, Rojo

📦 INCLUYE:
  • Bocina JBL Charge 6 (color elegido)
  • Cable USB-C de carga
  • Empaque seguro

🚚 ENVÍO GRATIS — 1-3 días hábiles

⚙️ ESPECIFICACIONES:
  • Potencia: 45 W RMS
  • Bluetooth 5.4 LE Audio + Auracast
  • Autonomía: hasta 28 horas
  • Resistencia: IP67
  • Carga USB-C
  • Conectividad PartyBoost

❓ DUDAS: pregunte antes de comprar.
   La única limitación: NO se conecta a la app JBL.
   Lo demás funciona 100%.

🛡️ Vendedor profesional MercadoLíder.
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

print(f"\n=== POST item: pics={len(all_pics)} variations={len(variations)} ===")
rp = requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"  HTTP {rp.status_code}")
if rp.status_code not in (200,201):
    print(f"  ❌ {rp.text[:1500]}")
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

requests.post(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text": DESCRIPTION},timeout=30)
print(f"\nListo, cuenta {me.get('nickname')}")
