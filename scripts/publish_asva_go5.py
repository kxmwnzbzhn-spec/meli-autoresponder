import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# 1) Fotos + GTIN + specs desde el CPID Go 5
CPID="MLM70426434"
p=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=15).json()
pics=[{"source":pic.get("url")} for pic in p.get("pictures",[])[:8] if pic.get("url")]
print(f"pics from CPID {CPID}: {len(pics)}",flush=True)

# Extract GTIN, MODEL, other useful attributes from catalog
cpid_attrs = {a["id"]:a for a in (p.get("attributes") or [])}
GTIN_VAL = None
if "GTIN" in cpid_attrs:
    GTIN_VAL = cpid_attrs["GTIN"].get("value_name")
print(f"GTIN from CPID: {GTIN_VAL}",flush=True)
print(f"CPID name: {p.get('name')}",flush=True)
print(f"CPID category: {p.get('parent_id') or p.get('category_id')}",flush=True)

TITLE = "BOCINA ORIGINAL JBL GO 5 – BLUETOOTH PORTÁTIL"
print(f"title: {TITLE} ({len(TITLE)} chars)",flush=True)

attrs = [
    {"id":"BRAND","value_name":"JBL"},
    {"id":"MODEL","value_name":"Go 5"},
    {"id":"LINE","value_name":"Go"},
    {"id":"ITEM_CONDITION","value_name":"Nuevo"},
]
if GTIN_VAL:
    attrs.append({"id":"GTIN","value_name":GTIN_VAL})

payload = {
    "family_name": TITLE,
    "category_id": "MLM59800",
    "price": 999,
    "currency_id": "MXN",
    "available_quantity": 1,
    "buying_mode": "buy_it_now",
    "condition": "new",
    "listing_type_id": "gold_pro",
    "pictures": pics,
    "attributes": attrs,
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"}
    ],
    "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False,"logistic_type":"drop_off"}
}
print(f"\n=== POSTING tradicional Go 5 (BRAND=JBL, 1 pza, $999) ===",flush=True)
post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=30).json()
if "id" not in post:
    print(f"❌ FAIL: {json.dumps(post)[:2000]}",flush=True)
    # Retry without LINE if that was rejected
    if "LINE" in json.dumps(post):
        attrs = [a for a in attrs if a["id"]!="LINE"]
        payload["attributes"] = attrs
        print("Retrying without LINE...",flush=True)
        post=requests.post("https://api.mercadolibre.com/items",headers=H,json=payload,timeout=30).json()
        if "id" not in post:
            print(f"❌ FAIL 2: {json.dumps(post)[:2000]}",flush=True)
            exit(1)
    else:
        exit(1)

new_id=post["id"]
print(f"✅ POSTED: {new_id} status={post.get('status')} price=${post.get('price')} qty={post.get('available_quantity')}",flush=True)
print(f"  title: {post.get('title','?')}",flush=True)
print(f"  URL: {post.get('permalink','?')}",flush=True)

DESC = """BOCINA JBL GO 5 – ORIGINAL

Bocina JBL GO 5 100% original, nueva en caja sellada. Producto auténtico con garantía del vendedor.

CARACTERÍSTICAS PRINCIPALES
- Marca: JBL
- Modelo: GO 5
- Conectividad: Bluetooth 5.3
- Diseño ultraportátil
- Batería de larga duración
- Resistente al agua y polvo (certificación IP67)
- Sonido JBL Pro Sound con graves potentes
- Compatible con la aplicación oficial JBL Portable

CONTENIDO DE LA CAJA
- 1 Bocina JBL GO 5
- Cable de carga USB-C
- Guía rápida
- Empaque original sellado

CONECTIVIDAD Y USO
Activa el Bluetooth de tu celular, tablet o computadora, busca "JBL GO 5" en la lista de dispositivos y conéctate. También puedes administrarla desde la app oficial JBL Portable disponible en App Store y Google Play.

IDEAL PARA
Uso diario, viajes, oficina, playa, alberca, actividades al aire libre, reuniones, gym.

GARANTÍA
30 días de garantía directa con el vendedor por defectos de fábrica.

ENVÍO
Envío rápido y seguro a través de MELI. Todos los productos se empacan cuidadosamente para llegar en perfecto estado.

PALABRAS CLAVE
JBL GO 5, JBL GO5, bocina JBL GO 5, bocina Bluetooth, bocina portátil, altavoz Bluetooth, altavoz portátil, mini bocina, bocina inalámbrica, bocina para celular, speaker Bluetooth, JBL Go, bocina impermeable, bocina waterproof, IP67."""

d=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",headers=H,json={"plain_text":DESC},timeout=15)
print(f"  description PUT: {d.status_code}",flush=True)
if d.status_code >= 400:
    print(f"    err: {d.text[:400]}",flush=True)
print(f"\nNEW_ITEM_ID={new_id}",flush=True)
