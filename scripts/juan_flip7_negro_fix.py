"""
FIX: La publicación Negro (MLM2894660055) puede tener fotos Azul.
Cerrarla y republicar con búsqueda más estricta de Negro real.
"""
import os, requests, time, json

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

OLD_NEGRO = "MLM2894660055"

# 1) Verificar las pics actuales
print(f"=== Verificando {OLD_NEGRO} ===")
g = requests.get(f"https://api.mercadolibre.com/items/{OLD_NEGRO}",headers=H,timeout=15).json()
print(f"  título: {g.get('title')}")
print(f"  pictures: {len(g.get('pictures',[]))}")
for p in (g.get("pictures") or [])[:3]:
    print(f"    {p.get('url','')}")

# 2) Cerrar viejo
print(f"\n=== Cerrando {OLD_NEGRO} ===")
rp = requests.put(f"https://api.mercadolibre.com/items/{OLD_NEGRO}",headers=H,json={"status":"paused"},timeout=15)
print(f"  pause: {rp.status_code}")
time.sleep(0.5)
rp = requests.put(f"https://api.mercadolibre.com/items/{OLD_NEGRO}",headers=H,json={"status":"closed"},timeout=15)
print(f"  close: {rp.status_code}")

# 3) Buscar pics Negro con verificación ESTRICTA: title debe tener "negr" pero NO "azul/blue/red/morado"
print("\n=== Buscando pics Negro estricto ===")
def search_strict_negro():
    urls = []
    for q in ["Jbl Flip 7 Negro Bluetooth", "Jbl Flip 7 Negra"]:
        rs = requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={requests.utils.quote(q)}&limit=15",headers=H,timeout=20).json()
        for p in rs.get("results",[])[:10]:
            pid = p.get("id")
            if not pid: continue
            prod = requests.get(f"https://api.mercadolibre.com/products/{pid}",headers=H,timeout=10).json()
            tl = (prod.get("name","") or "").lower()
            if "flip 7" not in tl and "flip7" not in tl: continue
            # ESTRICTO: debe tener negr y NO debe tener azul/blue/red/morado/purple/violeta
            if "negr" not in tl and "black" not in tl: continue
            if any(x in tl for x in ["azul", "blue", "rojo", "rojo", "red", "morado", "purple", "violeta", "rosa", "pink"]): 
                # Solo aceptar si el COLOR atributo es Negro
                attrs = prod.get("attributes",[])
                color_val = next((a.get("value_name","") for a in attrs if a.get("id")=="COLOR"), "")
                if "negr" not in color_val.lower() and "black" not in color_val.lower():
                    print(f"  skip '{prod.get('name','')[:60]}' (color={color_val})")
                    continue
            print(f"  ✓ catalog: '{prod.get('name','')[:60]}'")
            for pic in (prod.get("pictures") or [])[:5]:
                u = pic.get("url","")
                if u and u.startswith("http"): urls.append(u)
            if len(urls) >= 5: return urls[:5]
            time.sleep(0.2)
    # Fallback to listings
    print("  fallback listings")
    for q in ["JBL Flip 7 Negra", "JBL Flip 7 Negro Bocina"]:
        rs = requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={requests.utils.quote(q)}&limit=20",headers=H,timeout=20).json()
        for it in rs.get("results",[])[:10]:
            tl = (it.get("title","") or "").lower()
            if "flip 7" not in tl and "flip7" not in tl: continue
            if ("negr" not in tl and "black" not in tl) or any(x in tl for x in ["azul","rojo","morado","purple","rosa"]): continue
            iid = it.get("id")
            gd = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
            attrs = gd.get("attributes",[])
            color_val = next((a.get("value_name","") for a in attrs if a.get("id")=="COLOR"), "").lower()
            if color_val and "negr" not in color_val and "black" not in color_val: continue
            print(f"  ✓ listing: '{gd.get('title','')[:60]}' color={color_val}")
            for p in (gd.get("pictures") or [])[:5]:
                u = p.get("url","")
                if u and u.startswith("http"): urls.append(u)
            if len(urls) >= 5: return urls[:5]
            time.sleep(0.2)
    return urls[:5]

urls = search_strict_negro()
print(f"\n  URLs verificadas Negro: {len(urls)}")

def upload_url(url):
    try:
        img = requests.get(url, timeout=20).content
        if len(img) < 2000: return None
        rp = requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

pics = []
for u in urls[:5]:
    pid = upload_url(u)
    if pid: pics.append(pid)
    time.sleep(0.3)
print(f"  pics uploaded: {len(pics)}")

if not pics:
    print("❌ Sin pics — abortando")
    exit(1)

# Build same body as the recreate script
cat_id = "MLM59800"
cat_attrs = requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

attrs = [
    {"id":"BRAND","value_name":"JBL"},
    {"id":"MODEL","value_name":"Flip 7"},
    {"id":"LINE","value_name":"Flip"},
    {"id":"COLOR","value_name":"Negro"},
    {"id":"ITEM_CONDITION","value_name":"Reacondicionado"},
]
seen={x["id"] for x in attrs}
BAD={"EAN","UPC","MPN","SELLER_SKU","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","GTIN","FAMILY_NAME"}
for ca in cat_attrs:
    aid=ca.get("id"); tags=ca.get("tags") or {}
    req=tags.get("required") or tags.get("conditional_required")
    if not req or aid in seen or aid in BAD: continue
    vals=ca.get("values") or []; vt=ca.get("value_type")
    if vals: attrs.append({"id":aid,"value_id":vals[0]["id"],"value_name":vals[0].get("name","")})
    elif vt in ("number","number_unit"): attrs.append({"id":aid,"value_name":"1"})
    else: attrs.append({"id":aid,"value_name":"No aplica"})
    seen.add(aid)

body = {
    "category_id": cat_id,
    "family_name": "Bocina Jbl Flip 7 Bluetooth Ip67 Portatil Reacondicionada",
    "price": 399,
    "currency_id": "MXN",
    "available_quantity": 5,
    "buying_mode": "buy_it_now",
    "listing_type_id": "gold_pro",
    "condition": "refurbished",
    "pictures": [{"id": p} for p in pics],
    "shipping": {"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"cross_docking"},
    "attributes": attrs,
    "sale_terms": [
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"90 días"}
    ],
    "tags": ["immediate_payment"],
}

DESC = """JBL FLIP 7 - REACONDICIONADA - Color Negro

ESTÉTICA 10/10 - Apariencia perfecta, sin marcas ni rayones.

DEFECTOS DECLARADOS - LEA POR FAVOR:
- NO compatible con la aplicación JBL Portable
- NO compatible con Auracast (LE Audio)
- NO compatible con PartyBoost

SOLO funciona conexión Bluetooth básica.

TODO LO DEMÁS FUNCIONA AL 100%:
- Bluetooth 5.3 estable y rápido
- Sonido Original Pro Sound JBL (graves profundos)
- Resistencia agua y polvo IP67 (sumergible)
- Batería de 14 horas + 2 horas Playtime Boost
- Manos libres / Llamadas con micrófono
- Carga rápida USB-C
- Estructura física PERFECTA - luce como nueva

COLOR: Negro
Autonomía: hasta 16 horas
Potencia: 35 W RMS
Resistencia: IP67
Bluetooth: 5.3
Carga: USB-C
Conectividad: SOLO Bluetooth (NO Auracast, NO PartyBoost)

INCLUYE:
- 1 x Bocina JBL Flip 7 (Negro)
- 1 x Cable USB-C de carga

ENVÍO GRATIS en 1 a 3 días hábiles
Garantía 90 días contra defectos de operación

Pregunte ANTES de comprar si tiene dudas.
Las TRES limitaciones son: app JBL, Auracast y PartyBoost.
SOLO conexión Bluetooth básica.
"""

rp = requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
print(f"\n  POST → {rp.status_code}")
if rp.status_code not in (200,201):
    print(f"  ❌ {rp.text[:600]}"); exit(1)
j = rp.json()
iid = j.get("id")
print(f"  ✅ {iid} | '{j.get('title')}' | ${j.get('price')}")

rp = requests.put(f"https://api.mercadolibre.com/items/{iid}/description",
    headers=H, json={"plain_text": DESC}, timeout=30)
print(f"  desc PUT {rp.status_code}")
print(f"\nURL: {j.get('permalink')}")
