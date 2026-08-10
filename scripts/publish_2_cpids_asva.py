import os, requests, json, time
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# STEP 1: Close the failed catalog listing MLM3289470439
print("=== CLOSE the previous catalog attempt ===", flush=True)
for st in ("paused","closed"):
    r=requests.put("https://api.mercadolibre.com/items/MLM3289470439",headers=H,json={"status":st},timeout=10).json()
    print(f"  {st}: {r.get('status')} err={r.get('message','')}",flush=True)
    time.sleep(1)

# STEP 2: Fetch pictures from CPID for the new tradicional
CPID="MLM44713972"
p=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H,timeout=10).json()
pics_raw=p.get("pictures",[])[:8]
pics=[{"source": pic.get("url")} for pic in pics_raw if pic.get("url")]
print(f"\n=== CPID pics: {len(pics)} ===", flush=True)

# STEP 3: Publish as TRADICIONAL with custom title + all attrs
TITLE = "Bocina Jbl Go 4 Bluetooth Portatil Leer Descripcion Antes Compra"[:60]
print(f"title: {TITLE} ({len(TITLE)} chars)", flush=True)

payload = {
    "title": TITLE,
    "family_name": TITLE,
    "category_id": "MLM59800",
    "price": 399,
    "currency_id": "MXN",
    "available_quantity": 5,
    "buying_mode": "buy_it_now",
    "condition": "new",
    "listing_type_id": "gold_pro",
    "pictures": pics,
    "attributes": [
        {"id":"BRAND","value_name":"JBL"},
        {"id":"MODEL","value_name":"Go 4"},
        {"id":"LINE","value_name":"Go 4"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
        {"id":"POWER_SOURCE","value_name":"Bluetooth"},
    ],
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"}
    ],
    "shipping":{"mode":"me2","free_shipping":False,"local_pick_up":False,"logistic_type":"drop_off"}
}

print(f"\n=== POSTING tradicional ===", flush=True)
post = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload, timeout=25).json()
if "id" not in post:
    print(f"❌ FAIL: {json.dumps(post)[:1800]}", flush=True)
    exit(1)

new_id = post["id"]
print(f"✅ POSTED: {new_id} status={post.get('status')} price=${post.get('price')} qty={post.get('available_quantity')}", flush=True)
print(f"  title: {post.get('title','?')}", flush=True)
print(f"  URL: {post.get('permalink','?')}", flush=True)

# STEP 4: Custom description
DESC = """BOCINA JBL GO 4 BLUETOOTH – IMPORTANTE: LEER ANTES DE COMPRAR

INFORMACION IMPORTANTE SOBRE ESTA VARIANTE
Esta publicacion corresponde a una bocina JBL GO 4 fabricada en China. Esta variante NO ES COMPATIBLE CON LA APLICACION OFICIAL DE JBL.
Esto significa que la bocina funciona mediante conexion Bluetooth directa con tu celular, tablet u otro dispositivo compatible, pero NO puede vincularse, configurarse ni administrarse desde la aplicacion oficial de JBL.
Esta caracteristica es una de las razones por las que esta variante se ofrece a un PRECIO MAS ECONOMICO.
Por favor, considera esta informacion antes de realizar tu compra.

CARACTERISTICAS IMPORTANTES
- JBL GO 4
- Conexion inalambrica mediante Bluetooth
- Diseno compacto y portatil
- Fabricada en China
- NO compatible con la aplicacion oficial de JBL
- No requiere aplicacion para reproducir musica mediante Bluetooth
- Precio mas economico debido a las caracteristicas especificas de esta variante
- Ideal para uso cotidiano, viajes, oficina, habitacion, reuniones y actividades al aire libre

MUY IMPORTANTE: NO COMPATIBLE CON APP JBL
Esta variante NO se conecta con la aplicacion oficial de JBL.
Si necesitas especificamente una JBL GO 4 que pueda vincularse y administrarse mediante la aplicacion de JBL, esta variante NO es la indicada para ti.
La incompatibilidad con la aplicacion no significa necesariamente que la bocina tenga una falla. Es una caracteristica especifica de esta variante y se informa claramente desde antes de realizar la compra.

FABRICADA EN CHINA
Esta JBL GO 4 esta fabricada en China. Queremos que el comprador conozca esta informacion desde el inicio para que pueda tomar una decision de compra informada.

COMO SE UTILIZA
Simplemente activa el Bluetooth de tu telefono o dispositivo compatible, busca la bocina entre los dispositivos Bluetooth disponibles y realiza la conexion.
No necesitas utilizar la aplicacion de JBL para reproducir musica mediante una conexion Bluetooth convencional.

CONTENIDO
- 1 Bocina JBL GO 4
- Cable de carga
- Empaque correspondiente

IMPORTANTE ANTES DE FINALIZAR TU COMPRA
Al comprar este producto debes considerar expresamente lo siguiente:

1. Es una bocina JBL GO 4.
2. Esta fabricada en China.
3. Esta variante NO ES COMPATIBLE CON LA APP OFICIAL DE JBL.
4. Se utiliza mediante conexion Bluetooth directa.
5. Su precio es mas economico considerando las caracteristicas de esta variante.

Toda esta informacion se proporciona antes de la compra con el objetivo de que conozcas exactamente las caracteristicas del producto que estas adquiriendo y evitar confusiones o reclamos posteriores.
Si la compatibilidad con la aplicacion oficial de JBL es indispensable para ti, por favor NO COMPRES ESTA VARIANTE.

PALABRAS CLAVE
JBL GO 4, JBL GO4, bocina JBL GO 4, bocina Bluetooth, bocina portatil, altavoz Bluetooth, altavoz portatil, mini bocina, bocina inalambrica, bocina para celular, speaker Bluetooth, JBL Go, bocina portatil Bluetooth."""

d = requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",
                 headers=H, json={"plain_text": DESC}, timeout=15)
print(f"  description PUT: {d.status_code}", flush=True)
if d.status_code >= 400:
    print(f"    err: {d.text[:400]}", flush=True)

print(f"\nNEW_ITEM_ID={new_id}", flush=True)
