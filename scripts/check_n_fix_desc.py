import os, requests, json

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

# 1) Get current state
g = requests.get(f"https://api.mercadolibre.com/items/{IID}", headers=H).json()
print(f"Item {IID}:")
print(f"  title: {g.get('title')}")
print(f"  price: {g.get('price')}")
print(f"  qty:   {g.get('available_quantity')}")
print(f"  cond:  {g.get('condition')}")
print(f"  status:{g.get('status')}")
print(f"  link:  {g.get('permalink')}")
print(f"  pics:  {len(g.get('pictures') or [])}")

# 2) POST description (en lugar de PUT que dio 400)
DESC = """🎁 BOCINA JBL GO 4 ORIGINAL - CAJA ABIERTA - COLOR SORPRESA

🚨 LEER ANTES DE COMPRAR:

LIQUIDACIÓN DE INVENTARIO. Productos originales JBL en condición CAJA ABIERTA (devoluciones revisadas, en perfecto estado funcional). EL COLOR SE ASIGNA AL AZAR según disponibilidad.

⚠️ EL COLOR ES ALEATORIO. NO PUEDES ESCOGER COLOR. Te enviamos el que esté disponible. Colores que pueden tocarte: Negro, Azul, Rojo, Camuflaje, Aqua, Rosa, Azul Marino. NO SE ACEPTAN RECLAMOS POR COLOR — al comprar aceptas estas condiciones.

✅ INCLUYE:
• Bocina JBL Go 4 Original (color aleatorio)
• Cable USB-C de carga
• Caja JBL (abierta, puede tener marcas leves)
• Garantía 30 días contra defectos

✅ ESTADO REAL:
• 100% funcional, audio impecable
• Batería en perfecto estado
• Bluetooth 5.3 + AURACAST
• Resistencia IP67 intacta
• Estética muy buena

🔊 ESPECIFICACIONES JBL GO 4:
• Bluetooth 5.3 con AURACAST
• Resistencia IP67 polvo y agua
• Hasta 7 horas de reproducción
• JBL Pro Sound
• Carga USB-C, peso 190g

❌ NO INCLUYE:
• Color específico (es ALEATORIO)
• Caja sellada de fábrica

💰 $299 (vs $1,099 nueva). Liquidación.
📦 ENVÍO GRATIS Mercado Envíos.

⚖️ POLÍTICA DE RECLAMOS: SOLO se aceptan reclamos por: bocina que no enciende, batería defectuosa, falla bluetooth, parlante dañado. NO aceptamos reclamos por: color, estado de caja, marcas leves, accesorios faltantes excepto cable USB-C.

Si quieres color específico, busca nuestras otras publicaciones de Go 4 nuevas.
"""

# Intentar POST primero (creación), si ya existe será PUT
pr = requests.post(f"https://api.mercadolibre.com/items/{IID}/description",
                   headers=H, json={"plain_text": DESC})
print(f"\nPOST description → {pr.status_code}")
if pr.status_code >= 400:
    print(f"  body: {pr.text[:500]}")
    # Try PUT
    pr = requests.put(f"https://api.mercadolibre.com/items/{IID}/description",
                      headers=H, json={"plain_text": DESC})
    print(f"PUT description → {pr.status_code}")
    if pr.status_code >= 400:
        print(f"  body: {pr.text[:500]}")
else:
    print("  ✅ description set")

# TG notification
if TG and TGCID and g.get('permalink'):
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage", data={
        "chat_id": TGCID, "parse_mode":"Markdown",
        "text": (
            f"🎁 *Juan Go 4 Caja Abierta publicada*\n\n"
            f"`{IID}` — {g.get('title','?')}\n"
            f"Precio: ${g.get('price')} envío gratis\n"
            f"Stock visible: {g.get('available_quantity')}u (master 100u, auto-replenish)\n\n"
            f"[Ver]({g.get('permalink')})"
        ),
        "disable_web_page_preview":"true"
    }, timeout=20)
