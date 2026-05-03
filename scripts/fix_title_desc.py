import os, requests

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN"]
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

IID = "MLM2904707285"

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,
    "client_secret":APP_SECRET,"refresh_token":RT,
})
H = {"Authorization": f"Bearer {r.json()['access_token']}", "Content-Type":"application/json"}

# 1) Fix title - eliminar duplicado de "Color Sorpresa"
NEW_TITLE = "JBL Go 4 Bocina Bluetooth Caja Abierta Color Aleatorio IP67"  # 60 chars
NEW_FAMILY = "JBL Go 4 Bocina Bluetooth Caja Abierta IP67"  # mas corto
print(f"Nuevo titulo: '{NEW_TITLE}' ({len(NEW_TITLE)} chars)")
print(f"Nueva family_name: '{NEW_FAMILY}'")

# Estrategias multiples — primero family_name (MELI auto-genera title)
print("\n=== try 1: PUT family_name + COLOR=Aleatorio ===")
pr1 = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H, json={
    "family_name": NEW_FAMILY,
    "attributes": [
        {"id":"COLOR","value_name":"Aleatorio"},
    ]
})
print(f"  status={pr1.status_code}")
if pr1.status_code >= 400:
    print(f"  body: {pr1.text[:300]}")

# Try setting title directly
print("\n=== try 2: PUT title directo ===")
pr2 = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=H, json={
    "title": NEW_TITLE
})
print(f"  status={pr2.status_code}")
if pr2.status_code >= 400:
    print(f"  body: {pr2.text[:300]}")

# Verificar
g = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
print(f"\nTITLE actual: '{g.get('title')}'")
print(f"COLOR actual: {[a for a in g.get('attributes',[]) if a.get('id')=='COLOR']}")

# 2) Update description con AuraCast/app warnings
DESC = """BOCINA JBL GO 4 ORIGINAL - CAJA ABIERTA - COLOR ALEATORIO

LEER ANTES DE COMPRAR:

LIQUIDACION DE INVENTARIO. Productos originales JBL en condicion CAJA ABIERTA (devoluciones revisadas, en perfecto estado funcional). EL COLOR SE ASIGNA AL AZAR segun disponibilidad.

EL COLOR ES ALEATORIO. NO PUEDES ESCOGER COLOR. Te enviamos el que este disponible. Colores que pueden tocarte: Negro, Azul, Rojo, Camuflaje, Aqua, Rosa, Azul Marino. NO SE ACEPTAN RECLAMOS POR COLOR -- al comprar aceptas estas condiciones.

IMPORTANTE - COMPATIBILIDAD CON APPS:
Esta unidad NO ES COMPATIBLE con la app oficial JBL Portable ni con la funcion AURACAST. Funciona perfecto como bocina Bluetooth standalone con cualquier dispositivo (telefono, tablet, computadora) pero la conexion a la app oficial JBL Portable y la sincronizacion AURACAST entre varias bocinas NO ESTAN HABILITADAS en esta serie de fabrica. NO SE ACEPTAN RECLAMOS POR INCOMPATIBILIDAD CON APP NI POR AURACAST.

INCLUYE:
- Bocina JBL Go 4 Original (color aleatorio)
- Cable USB-C de carga
- Caja JBL (abierta, puede tener marcas leves)
- Garantia 30 dias contra defectos funcionales

ESTADO REAL:
- 100 por ciento funcional como bocina Bluetooth
- Bateria en perfecto estado
- Bluetooth standalone compatible con cualquier dispositivo
- Resistencia IP67 intacta
- Estetica muy buena

ESPECIFICACIONES JBL GO 4:
- Bluetooth standalone (no app, no AuraCast)
- Resistencia IP67 polvo y agua
- Hasta 7 horas de reproduccion
- JBL Pro Sound
- Carga USB-C, peso 190 gramos

NO INCLUYE:
- Color especifico (es ALEATORIO)
- Caja sellada de fabrica
- Compatibilidad con app JBL Portable
- AuraCast multipoint

PRECIO LIQUIDACION: 299 pesos. ENVIO GRATIS por Mercado Envios.

POLITICA DE RECLAMOS: Solo se aceptan reclamos por bocina que no enciende, bateria defectuosa, falla bluetooth basica, parlante danado. NO aceptamos reclamos por: color recibido, estado de caja, marcas leves esteticas, accesorios faltantes excepto cable USB-C, incompatibilidad con app JBL Portable, ni AuraCast.

Si quieres color especifico nuevo sellado y app/AuraCast oficial, busca nuestras otras publicaciones JBL Go 4 nuevas.
"""

print("\n=== PUT description ===")
pd = requests.put(f"https://api.mercadolibre.com/items/{IID}/description",
                   headers=H, json={"plain_text": DESC})
print(f"  status={pd.status_code}")
if pd.status_code >= 400:
    print(f"  body: {pd.text[:400]}")
else:
    print("  OK desc updated")

if TG and TGCID:
    g = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id": TGCID, "parse_mode":"Markdown",
        "text": (
            f"Juan Go 4 Caja Abierta — actualizado:\n\n"
            f"`{IID}`\n"
            f"Title: {g.get('title')}\n"
            f"Desc: con clausula AuraCast/app NO compatible\n"
            f"https://articulo.mercadolibre.com.mx/MLM-2904707285"
        ),
    }, timeout=20)
