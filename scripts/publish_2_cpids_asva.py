import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

CPID = "MLM44713972"

# Publish catalog listing
payload = {
    "catalog_product_id": CPID,
    "category_id": "MLM59800",
    "price": 399,
    "currency_id": "MXN",
    "available_quantity": 5,
    "buying_mode": "buy_it_now",
    "condition": "new",
    "listing_type_id": "gold_pro",
    "catalog_listing": True,
    "sale_terms": [
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"}
    ]
}
print(f"POSTING catalog CPID={CPID} price=$399 qty=5", flush=True)
p = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload, timeout=25).json()
if "id" not in p:
    print(f"❌ FAIL: {json.dumps(p)[:1500]}", flush=True)
    exit(1)

new_id = p["id"]
print(f"✅ POSTED: {new_id} status={p.get('status')} price=${p.get('price')} qty={p.get('available_quantity')}", flush=True)
print(f"  MELI title: {p.get('title','?')[:80]}", flush=True)
print(f"  URL: {p.get('permalink','?')}", flush=True)

# Set the custom description
DESC = """BOCINA JBL GO 4 BLUETOOTH – IMPORTANTE: LEER ANTES DE COMPRAR

INFORMACIÓN IMPORTANTE SOBRE ESTA VARIANTE
Esta publicación corresponde a una bocina JBL GO 4 fabricada en China. Esta variante NO ES COMPATIBLE CON LA APLICACIÓN OFICIAL DE JBL.
Esto significa que la bocina funciona mediante conexión Bluetooth directa con tu celular, tablet u otro dispositivo compatible, pero NO puede vincularse, configurarse ni administrarse desde la aplicación oficial de JBL.
Esta característica es una de las razones por las que esta variante se ofrece a un PRECIO MÁS ECONÓMICO.
Por favor, considera esta información antes de realizar tu compra.

CARACTERÍSTICAS IMPORTANTES
• JBL GO 4
• Conexión inalámbrica mediante Bluetooth
• Diseño compacto y portátil
• Fabricada en China
• NO compatible con la aplicación oficial de JBL
• No requiere aplicación para reproducir música mediante Bluetooth
• Precio más económico debido a las características específicas de esta variante
• Ideal para uso cotidiano, viajes, oficina, habitación, reuniones y actividades al aire libre

MUY IMPORTANTE: NO COMPATIBLE CON APP JBL
Esta variante NO se conecta con la aplicación oficial de JBL.
Si necesitas específicamente una JBL GO 4 que pueda vincularse y administrarse mediante la aplicación de JBL, esta variante NO es la indicada para ti.
La incompatibilidad con la aplicación no significa necesariamente que la bocina tenga una falla. Es una característica específica de esta variante y se informa claramente desde antes de realizar la compra.

FABRICADA EN CHINA
Esta JBL GO 4 está fabricada en China. Queremos que el comprador conozca esta información desde el inicio para que pueda tomar una decisión de compra informada.

¿CÓMO SE UTILIZA?
Simplemente activa el Bluetooth de tu teléfono o dispositivo compatible, busca la bocina entre los dispositivos Bluetooth disponibles y realiza la conexión.
No necesitas utilizar la aplicación de JBL para reproducir música mediante una conexión Bluetooth convencional.

CONTENIDO
• 1 Bocina JBL GO 4
• Cable de carga
• Empaque correspondiente

IMPORTANTE ANTES DE FINALIZAR TU COMPRA
Al comprar este producto debes considerar expresamente lo siguiente:

1. Es una bocina JBL GO 4.
2. Está fabricada en China.
3. Esta variante NO ES COMPATIBLE CON LA APP OFICIAL DE JBL.
4. Se utiliza mediante conexión Bluetooth directa.
5. Su precio es más económico considerando las características de esta variante.

Toda esta información se proporciona antes de la compra con el objetivo de que conozcas exactamente las características del producto que estás adquiriendo y evitar confusiones o reclamos posteriores.
Si la compatibilidad con la aplicación oficial de JBL es indispensable para ti, por favor NO COMPRES ESTA VARIANTE.

PALABRAS CLAVE DE BÚSQUEDA
JBL GO 4, JBL GO4, bocina JBL GO 4, bocina Bluetooth, bocina portátil, altavoz Bluetooth, altavoz portátil, mini bocina, bocina inalámbrica, bocina para celular, speaker Bluetooth, JBL Go, bocina portátil Bluetooth."""

d = requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",
                 headers=H, json={"plain_text": DESC}, timeout=15)
print(f"  description PUT: {d.status_code}", flush=True)
if d.status_code >= 400:
    print(f"    err: {d.text[:300]}", flush=True)

print(f"\nNEW_ITEM_ID={new_id}", flush=True)
