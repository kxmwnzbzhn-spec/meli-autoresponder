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

# Description SIN emojis ni caracteres especiales (MELI los rechaza en plain_text)
DESC = """BOCINA JBL GO 4 ORIGINAL - CAJA ABIERTA - COLOR SORPRESA

LEER ANTES DE COMPRAR:

LIQUIDACION DE INVENTARIO. Productos originales JBL en condicion CAJA ABIERTA (devoluciones revisadas, en perfecto estado funcional). EL COLOR SE ASIGNA AL AZAR segun disponibilidad.

EL COLOR ES ALEATORIO. NO PUEDES ESCOGER COLOR. Te enviamos el que este disponible. Colores que pueden tocarte: Negro, Azul, Rojo, Camuflaje, Aqua, Rosa, Azul Marino. NO SE ACEPTAN RECLAMOS POR COLOR -- al comprar aceptas estas condiciones.

INCLUYE:
- Bocina JBL Go 4 Original (color aleatorio)
- Cable USB-C de carga
- Caja JBL (abierta, puede tener marcas leves)
- Garantia 30 dias contra defectos

ESTADO REAL:
- 100 por ciento funcional, audio impecable
- Bateria en perfecto estado
- Bluetooth 5.3 con AURACAST
- Resistencia IP67 intacta
- Estetica muy buena

ESPECIFICACIONES JBL GO 4:
- Bluetooth 5.3 con AURACAST
- Resistencia IP67 polvo y agua
- Hasta 7 horas de reproduccion
- JBL Pro Sound
- Carga USB-C, peso 190 gramos

NO INCLUYE:
- Color especifico (es ALEATORIO)
- Caja sellada de fabrica

PRECIO LIQUIDACION: 299 pesos (vs 1099 nueva sellada).
ENVIO GRATIS por Mercado Envios.

POLITICA DE RECLAMOS: Solo se aceptan reclamos por bocina que no enciende, bateria defectuosa, falla bluetooth, parlante danado. No aceptamos reclamos por color recibido, estado de caja, marcas leves esteticas, ni accesorios faltantes excepto cable USB-C.

Si quieres color especifico nuevo sellado, busca nuestras otras publicaciones de JBL Go 4.
"""

pr = requests.post(f"https://api.mercadolibre.com/items/{IID}/description",
                   headers=H, json={"plain_text": DESC})
print(f"POST description -> {pr.status_code}")
if pr.status_code >= 400:
    print(f"  body: {pr.text[:400]}")
    pr = requests.put(f"https://api.mercadolibre.com/items/{IID}/description",
                      headers=H, json={"plain_text": DESC})
    print(f"PUT description -> {pr.status_code}")
    if pr.status_code >= 400:
        print(f"  body: {pr.text[:400]}")
else:
    print("  OK description set")

if TG and TGCID:
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id": TGCID, "parse_mode":"Markdown",
        "text": (
            "JUAN Go 4 Caja Abierta lista:\n\n"
            "Item: `MLM2904707285`\n"
            "Precio: $299 envio gratis\n"
            "Stock: 100u (1 visible)\n"
            "Condition: used\n"
            "https://articulo.mercadolibre.com.mx/MLM-2904707285"
        ),
    }, timeout=20)
