"""
Publicar JBL Charge 6 en cuenta Juan — 3 publicaciones SEPARADAS por color
- Negro, Azul, Rojo
- $399 c/u
- Envío gratis
- Reacondicionado
- Sin variaciones para evitar family_name conflict
"""
import os, requests, time

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
print(f"Cuenta: {me.get('nickname')}")

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

cat_id="MLM59800"
cat_attrs=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}/attributes",headers=H,timeout=15).json()

DESCRIPTION_TPL = """═══════════════════════════════════════
JBL Charge 6 — REACONDICIONADA — Color {COLOR}
═══════════════════════════════════════

⚠️ IMPORTANTE — LEA ANTES DE COMPRAR ⚠️

Producto REACONDICIONADO con UN solo defecto:

❌ NO es compatible con la aplicación JBL Portable
❌ Sin garantía oficial

✅ TODO lo demás funciona PERFECTAMENTE:
  • Bluetooth 100% operativo
  • Sonido potente original JBL
  • Bajos profundos
  • Resistencia agua y polvo IP67
  • Batería hasta 28 horas
  • Powerbank funcional (USB-C)
  • PartyBoost
  • Manos libres

🎨 COLOR: {COLOR}

📦 INCLUYE:
  • Bocina JBL Charge 6 ({COLOR})
  • Cable USB-C
  • Empaque seguro

🚚 ENVÍO GRATIS — 1 a 3 días hábiles

⚙️ ESPECIFICACIONES:
  • Potencia 45 W RMS
  • Bluetooth 5.4 LE Audio + Auracast
  • Autonomía 28 horas
  • IP67 (sumergible)
  • USB-C carga rápida

❓ DUDAS: pregunte antes de comprar.
   Única limitación: NO se conecta a la app JBL.
   Lo demás funciona 100%.

🛡️ Vendedor profesional MercadoLíder.
"""

def build_attrs(color):
    a = [
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

results = []
for color, q in [("Negro","Jbl Charge 6 Negra"), ("Azul","Jbl Charge 6 Azul"), ("Rojo","Jbl Charge 6 Roja")]:
    print(f"\n=== {color} ===")
    urls = search_catalog_urls(q)
    pics_juan = []
    for u in urls[:5]:
        pid = upload_url(u)
        if pid: pics_juan.append(pid)
        time.sleep(0.3)
    if not pics_juan:
        print(f"  ❌ {color}: sin pics — saltando")
        continue
    print(f"  pics: {len(pics_juan)}")
    
    title = f"Jbl Charge 6 Bluetooth Portatil {color} Reacondicionada Sin App"[:60]
    desc = DESCRIPTION_TPL.format(COLOR=color)
    
    body = {

        "family_name": "JBL Charge 6 Reacondicionada",
        "sale_terms": [{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
        "category_id": cat_id,
        "price": 399,
        "currency_id": "MXN",
        "available_quantity": 5,
        "buying_mode": "buy_it_now",
        "listing_type_id": "gold_pro",
        "condition": "refurbished",
        "pictures": [{"id": p} for p in pics_juan],
        "shipping": {"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"cross_docking"},
        "attributes": build_attrs(color),
        "tags": ["immediate_payment"],
        "description": {"plain_text": desc}
    }
    rp = requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
    print(f"  POST → {rp.status_code}")
    if rp.status_code not in (200,201):
        print(f"  ❌ {rp.text}")
        continue
    j = rp.json()
    iid = j.get("id")
    print(f"  ✅ {iid} | ${j.get('price')} | stock={j.get('available_quantity')}")
    requests.post(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,json={"plain_text": desc},timeout=30)
    results.append((color, iid, j.get("permalink")))
    time.sleep(2)

print(f"\n=== RESUMEN ===")
for c, iid, url in results:
    print(f"  {c}: {iid} | {url}")
