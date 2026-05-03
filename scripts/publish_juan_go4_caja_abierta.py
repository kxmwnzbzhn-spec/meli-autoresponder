#!/usr/bin/env python3
"""Publica en JUAN una bocina JBL Go 4 caja abierta color aleatorio.
- Liquidación de devoluciones (~71 reales + extras hasta 100u)
- Precio $299 + envío gratis
- Condition: used (caja abierta)
- Stock 100 reales, 1 visible, auto-replenish
- Título y descripción SEO blindados contra reclamos por color
- Fotos: 1ra fondo blanco oficial + galería de colores
"""
import os, requests, json, time

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN"]  # JUAN
TG = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TGCID = os.environ.get("TELEGRAM_CHAT_ID", "")

PRICE = 299.0
TOTAL_STOCK = 100
VISIBLE_QTY = 1
CATEGORY = "MLM59800"  # Bocinas Bluetooth

# Catálogos por color (oficial MELI = foto fondo blanco)
COLOR_CATALOGS = [
    ("MLM44710240", "Negro"),
    ("MLM44710367", "Azul"),
    ("MLM44710313", "Rojo"),
    ("MLM37361021", "Camuflaje"),
    ("MLM61262890", "Aqua"),
    ("MLM44710421", "Azul Marino"),
]

TITLE = "JBL Go 4 Bocina Bluetooth Portátil Caja Abierta Color Sorpresa"  # 62
TITLE = TITLE[:60]

DESCRIPTION = """🎁 BOCINA JBL GO 4 ORIGINAL - CAJA ABIERTA - COLOR SORPRESA - PRECIO LIQUIDACIÓN $299

🚨 LEER ANTES DE COMPRAR (IMPORTANTE):

Esta es una publicación de LIQUIDACIÓN DE INVENTARIO. Los productos son originales JBL pero vienen en condición CAJA ABIERTA (devoluciones revisadas en perfecto estado funcional) y el COLOR SE ASIGNA AL AZAR según la disponibilidad del momento.

⚠️ EL COLOR ES ALEATORIO. NO PUEDES ESCOGER COLOR. Te enviamos el que esté disponible al momento de tu pedido. Colores que pueden tocarte: Negro, Azul, Rojo, Camuflaje, Aqua, Rosa, Azul Marino. NO SE ACEPTAN RECLAMOS POR COLOR — al comprar aceptas estas condiciones.

✅ QUE INCLUYE:
• Bocina JBL Go 4 Original (color aleatorio)
• Cable de carga USB-C
• Caja JBL (abierta, puede tener marcas leves de exhibición)
• Garantía vendedor 30 días contra defectos de funcionamiento

✅ ESTADO REAL DEL PRODUCTO:
• 100% funcional, audio impecable
• Batería en perfecto estado
• Bluetooth y emparejamiento OK
• Resistencia IP67 al agua y polvo intacta
• Estética: muy bueno (caja abierta, sin uso del producto o uso mínimo)

🔊 ESPECIFICACIONES JBL GO 4:
• Bluetooth 5.3 con AURACAST
• Resistencia IP67 polvo y agua
• Hasta 7 horas de reproducción
• Sonido JBL Pro Sound
• Carga USB-C
• Peso solo 190 gramos
• Incluye correa de mano

❌ NO INCLUYE:
• La caja PUEDE estar dañada o no estar
• No se garantiza color específico
• No se aceptan cambios por color

💰 PRECIO LIQUIDACIÓN: $299 (vs $1,099 nueva sellada). Aprovecha.

📦 ENVÍO GRATIS por Mercado Envíos. Despacho mismo día (días hábiles antes de las 2pm).

⚖️ POLÍTICA DE RECLAMOS:
SOLO se aceptan reclamos por: bocina que no enciende, batería defectuosa, falla de bluetooth, daño en parlante. NO aceptamos reclamos por: color recibido, estado de caja, marcas estéticas leves, accesorios faltantes (excepto cable USB-C).

Al comprar aceptas las condiciones descritas. Si quieres color específico nuevo sellado, busca nuestras otras publicaciones de JBL Go 4 nuevas.

¡Aprovecha esta oportunidad de tener una JBL Go 4 original a precio único!
"""

# Auth
print("=== Auth JUAN ===")
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": APP_ID, "client_secret": APP_SECRET, "refresh_token": RT,
})
at = r.json()["access_token"]
H = {"Authorization": f"Bearer {at}", "Content-Type": "application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
print(f"Cuenta: {me.get('nickname')} ({me.get('id')})\n")

# === Coleccionar fotos de los 6 colores ===
print("=== Recolectar fotos por color ===")
photos = []
for cpid, color in COLOR_CATALOGS:
    try:
        p = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H, timeout=15).json()
        pics = p.get("pictures") or []
        if pics:
            url = pics[0].get("url") or pics[0].get("secure_url")
            if url:
                photos.append({"source": url, "_color": color})
                print(f"  ✅ {color}: {url[:70]}")
        time.sleep(0.3)
    except Exception as e:
        print(f"  ❌ {color}: {e}")

print(f"\nFotos recolectadas: {len(photos)}")

# Foto principal (fondo blanco oficial Negro)
# Pongo Negro primero — el catalog product es la foto oficial MELI con fondo blanco
photos = sorted(photos, key=lambda p: 0 if p['_color'] == "Negro" else 1)

payload = {
    # NOTA: MELI no acepta `title` cuando family_name esta presente
    # (lo auto-genera). Si quieres custom title, hay que quitar family_name
    # y atributo FAMILY_NAME pero entonces pide otro required field.
    # Esta es la aproximación mas segura: family_name auto-genera titulo SEO.
    "family_name": "JBL Go 4 Bocina Bluetooth Caja Abierta Color Sorpresa",
    "category_id": CATEGORY,
    "price": PRICE,
    "available_quantity": VISIBLE_QTY,
    "currency_id": "MXN",
    "condition": "used",  # caja abierta
    "listing_type_id": "gold_special",
    "pictures": [{"source": p["source"]} for p in photos[:8]],
    "sale_terms": [
        {"id": "WARRANTY_TYPE", "value_name": "Garantía del vendedor"},
        {"id": "WARRANTY_TIME", "value_name": "30 días"},
    ],
    "attributes": [
        {"id": "BRAND",         "value_name": "JBL"},
        {"id": "MODEL",         "value_name": "Go 4"},
        {"id": "LINE",          "value_name": "Go"},
        {"id": "COLOR",         "value_name": "Color Sorpresa"},
        {"id": "GTIN",          "value_name": "No aplica"},
        {"id": "WITH_BLUETOOTH","value_name": "Sí"},
        {"id": "BATTERY_LIFE",  "value_name": "7 h"},
    ],
    "shipping": {
        "mode": "me2",
        "free_shipping": True,
        "tags": ["self_service_in"],
    },
}

print("\n=== POST item ===")
pr = requests.post("https://api.mercadolibre.com/items", headers=H, json=payload)
print(f"  status: {pr.status_code}")
j = pr.json()
if pr.status_code in (200, 201):
    iid = j.get("id")
    permalink = j.get("permalink")
    print(f"  ✅ {iid}")
    print(f"     {permalink}")

    # Subir descripción
    desc = requests.put(
        f"https://api.mercadolibre.com/items/{iid}/description",
        headers=H, json={"plain_text": DESCRIPTION}
    )
    print(f"  PUT description → {desc.status_code}")

    # Update stock_config_juan.json
    config_file = "stock_config_juan.json"
    try:
        with open(config_file) as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    cfg[iid] = {
        "label": "Go 4 Caja Abierta Color Sorpresa",
        "real_stock": TOTAL_STOCK - VISIBLE_QTY,
        "min_visible": VISIBLE_QTY,
        "auto_replenish": True,
        "replenish_quantity": VISIBLE_QTY,
        "catalog_war": False,
        "color": "Color Sorpresa",
        "model": "Go 4",
        "condition": "caja_abierta",
        "label_seo": "liquidacion devoluciones",
    }
    with open(config_file, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    print(f"  ✅ stock_config_juan.json actualizado")

    if TG and TGCID:
        msg = (
            f"🎁 *Nueva publicación Juan: Go 4 Caja Abierta*\n\n"
            f"*ID:* `{iid}`\n"
            f"*Precio:* ${PRICE:.0f} envío gratis\n"
            f"*Stock:* {TOTAL_STOCK}u (1 visible + auto-replenish)\n"
            f"*Estado:* caja abierta, color aleatorio\n"
            f"*Descripción:* SEO + clausula NO RECLAMOS por color\n\n"
            f"[Ver publicación]({permalink})"
        )
        requests.post(
            f"https://api.telegram.org/bot{TG}/sendMessage",
            data={"chat_id": TGCID, "parse_mode": "Markdown",
                  "text": msg, "disable_web_page_preview": "true"},
            timeout=20,
        )
else:
    print(f"  ❌ ERROR")
    print(json.dumps(j, indent=2, ensure_ascii=False)[:2000])
    if TG and TGCID:
        requests.post(
            f"https://api.telegram.org/bot{TG}/sendMessage",
            data={"chat_id": TGCID, "parse_mode": "Markdown",
                  "text": f"❌ *Falló publicación Go 4 Caja Abierta Juan*\n\n```\n{json.dumps(j, ensure_ascii=False)[:1500]}\n```"},
            timeout=20,
        )
