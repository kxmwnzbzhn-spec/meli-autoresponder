"""
Charge 6 — Cerrar las 3 actuales y recrear con family_name SEO + nueva descripción
"""
import os, requests, time, json

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

OLD = ["MLM2894615677","MLM2894615713","MLM5252530944"]

# 1) Pausar y cerrar las viejas
print("=== Cerrando viejas ===")
for iid in OLD:
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"paused"},timeout=15)
    print(f"  pause {iid}: {rp.status_code}")
    time.sleep(0.5)
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"status":"closed"},timeout=15)
    print(f"  close {iid}: {rp.status_code}")
    time.sleep(0.5)

# 2) Re-buscar pics por color (usar /products/search)
print("\n=== Buscando pics ===")
def search_catalog_urls(query):
    rs = requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={requests.utils.quote(query)}&limit=5",headers=H,timeout=20).json()
    urls=[]
    for p in rs.get("results",[])[:3]:
        pid=p.get("id")
        if not pid: continue
        prod=requests.get(f"https://api.mercadolibre.com/products/{pid}",headers=H,timeout=10).json()
        for pic in (prod.get("pictures") or [])[:5]:
            u=pic.get("url","")
            if u and u.startswith("http"): urls.append(u)
        if urls: break
    return urls[:6]

def upload_url(url):
    try:
        img=requests.get(url,timeout=20).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

# 3) Atributos
cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

def build_attrs(color):
    a=[
        {"id":"BRAND","value_name":"JBL"},
        {"id":"MODEL","value_name":"Charge 6"},
        {"id":"LINE","value_name":"Charge"},
        {"id":"COLOR","value_name":color},
        {"id":"ITEM_CONDITION","value_name":"Reacondicionado"},
    ]
    seen={x["id"] for x in a}
    BAD={"EAN","UPC","MPN","SELLER_SKU","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","GTIN","FAMILY_NAME"}
    for ca in cat_attrs:
        aid=ca.get("id"); tags=ca.get("tags") or {}
        req=tags.get("required") or tags.get("conditional_required")
        if not req or aid in seen or aid in BAD: continue
        vals=ca.get("values") or []; vt=ca.get("value_type")
        if vals: a.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
        elif vt in ("number","number_unit"): a.append({"id":aid,"value_name":"1"})
        else: a.append({"id":aid,"value_name":"No aplica"})
        seen.add(aid)
    return a

def desc(color):
    return f"""═══════════════════════════════════════
JBL CHARGE 6 — REACONDICIONADA — Color {color}
═══════════════════════════════════════

🌟 ESTÉTICA 10/10 — Apariencia PERFECTA, sin marcas ni rayones 🌟

⚠️ POR FAVOR LEA — DEFECTOS DECLARADOS ⚠️

Este equipo es REACONDICIONADO con SOLO 2 limitaciones:

❌ NO compatible con la aplicación JBL Portable
❌ NO compatible con Auracast (LE Audio)

✅ TODO LO DEMÁS FUNCIONA AL 100%:
  ✓ Bluetooth 5.3 estable y rápido
  ✓ Sonido Original Pro Sound JBL (graves profundos)
  ✓ Resistencia agua y polvo IP67 (sumergible)
  ✓ Batería de 28 horas de duración
  ✓ Powerbank funcional vía USB-C
  ✓ PartyBoost (conecta con otras JBL compatibles)
  ✓ Manos libres / Llamadas con micrófono
  ✓ Carga rápida USB-C
  ✓ Estructura física PERFECTA — luce como nueva

🎨 COLOR: {color}
🔋 Autonomía: hasta 28 horas
🔊 Potencia: 45 W RMS
💧 Resistencia: IP67 (sumergible 1m por 30min)
📶 Bluetooth: 5.3
🔌 Carga: USB-C
🎵 Conectividad: PartyBoost (NO Auracast)

📦 INCLUYE:
  • 1 x Bocina JBL Charge 6 ({color})
  • 1 x Cable USB-C de carga
  • Empaque seguro reforzado

🚚 ENVÍO GRATIS en 1 a 3 días hábiles
🛡️ Garantía 90 días contra defectos de operación

❓ ¿LE INTERESA?
   Pregunte ANTES de comprar si tiene dudas.
   Las DOS únicas limitaciones son la app JBL y Auracast.
   El sonido, calidad de audio y todas las demás funciones
   son IDÉNTICAS al modelo de tienda.

🏆 Vendedor MercadoLíder con miles de ventas exitosas.
   Compre con total confianza.
"""

# 4) family_name SEO — el título auto será family_name + COLOR
NEW_FAMILY = "Bocina Jbl Charge 6 Bluetooth Ip67 Portatil Reacondicionada"

results=[]
for color, q in [("Negro","Jbl Charge 6 Negra"),("Azul","Jbl Charge 6 Azul"),("Rojo","Jbl Charge 6 Roja")]:
    print(f"\n=== {color} ===")
    urls = search_catalog_urls(q)
    pics_juan=[]
    for u in urls[:5]:
        pid = upload_url(u)
        if pid: pics_juan.append(pid)
        time.sleep(0.3)
    if not pics_juan:
        print(f"  ❌ sin pics, skip"); continue
    print(f"  pics: {len(pics_juan)}")
    
    body = {
        "category_id": cat_id,
        "family_name": NEW_FAMILY,
        "price": 399,
        "currency_id": "MXN",
        "available_quantity": 5,
        "buying_mode": "buy_it_now",
        "listing_type_id": "gold_pro",
        "condition": "refurbished",
        "pictures": [{"id": p} for p in pics_juan],
        "shipping": {"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"cross_docking"},
        "attributes": build_attrs(color),
        "sale_terms": [
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"90 días"}
        ],
        "tags": ["immediate_payment"],
    }
    rp = requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
    print(f"  POST → {rp.status_code}")
    if rp.status_code not in (200,201):
        print(f"  ❌ {rp.text[:600]}"); continue
    j = rp.json()
    iid = j.get("id")
    title = j.get("title","")
    print(f"  ✅ {iid} | título: '{title}' | ${j.get('price')}")
    
    # Set description via PUT json text
    desc_text = desc(color)
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}/description",
        headers=H, json={"text": desc_text}, timeout=30)
    print(f"  desc PUT {rp.status_code}")
    
    results.append((color, iid, title, j.get("permalink")))
    time.sleep(2)

print("\n=== RESUMEN FINAL ===")
for c,iid,t,url in results:
    print(f"  {c}: {iid}")
    print(f"    título: {t}")
    print(f"    URL: {url}")
