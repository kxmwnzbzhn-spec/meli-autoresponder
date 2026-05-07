"""Corrige título + descripción del item MLM5296392666.
GET con Bearer del owner (sin auth retorna 403 si el item está restringido).
"""
import os, requests, json

APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
TG=os.environ.get("TELEGRAM_BOT_TOKEN","")
TGCID=os.environ.get("TELEGRAM_CHAT_ID","")

ITEM_ID = "MLM5296392666"

ACCS = {
    "JUAN":     os.environ.get("MELI_REFRESH_TOKEN_JUAN") or os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL": os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":     os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO": os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
    "DILCIE":   os.environ.get("MELI_REFRESH_TOKEN_DILCIE"),
    "MILDRED":  os.environ.get("MELI_REFRESH_TOKEN_MILDRED"),
    "BREN":     os.environ.get("MELI_REFRESH_TOKEN_BREN"),
    "WILBERT":  os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "ASGARI":   os.environ.get("MELI_REFRESH_TOKEN_ASGARI"),
    "ANGEL":    os.environ.get("MELI_REFRESH_TOKEN_ANGEL"),
    "YC_NEW":   os.environ.get("MELI_REFRESH_TOKEN_YC_NEW"),
}

def tok(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")

# Iterar cada cuenta con su Bearer y probar GET al item
owner_acc = None
owner_at = None
item_data = None

for acc, rt in ACCS.items():
    if not rt: continue
    at = tok(rt)
    if not at: continue
    H = {"Authorization": f"Bearer {at}"}
    me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
    uid = me.get("id")
    if not uid: continue
    # GET item CON auth
    r = requests.get(f"https://api.mercadolibre.com/items/{ITEM_ID}", headers=H, timeout=15)
    if r.status_code != 200:
        print(f"  {acc} ({uid}): GET → HTTP {r.status_code}")
        continue
    j = r.json()
    if j.get("seller_id") == uid:
        owner_acc = acc
        owner_at = at
        item_data = j
        print(f"\n✅ Dueño encontrado: {acc} (uid {uid})")
        print(f"  Título actual: {j.get('title')}")
        print(f"  Status: {j.get('status')}  sub_status: {j.get('sub_status')}")
        print(f"  Price: ${j.get('price')}")
        print(f"  Permalink: {j.get('permalink','')[:120]}")
        break
    else:
        print(f"  {acc}: item visible pero seller_id {j.get('seller_id')} != {uid}")

if not owner_at:
    print(f"❌ Ninguna cuenta es dueña de {ITEM_ID}")
    exit(1)

H = {"Authorization": f"Bearer {owner_at}", "Content-Type":"application/json"}

# Bajar descripción actual
desc_r = requests.get(f"https://api.mercadolibre.com/items/{ITEM_ID}/description", headers=H, timeout=15).json()
print(f"\nDescripción actual ({len(desc_r.get('plain_text','') or '')} chars):")
print((desc_r.get("plain_text","") or "")[:400])
print("...")

# Nuevo título profesional
NEW_TITLE = "Bocina Bluetooth Portátil Inalámbrica Recargable IP67 40W"

# Descripción honesta y profesional
NEW_DESC = """🔊 BOCINA BLUETOOTH PORTÁTIL — VERSIÓN COMPATIBLE 1.1

⚠️ INFORMACIÓN IMPORTANTE — Por favor lee antes de comprar.
Te informamos con total transparencia: este producto es una bocina bluetooth tipo réplica (calidad 1.1 / espejo) que imita el diseño de modelos premium reconocidos.

✗ NO es producto original de marca
✗ NO es compatible con la app oficial de la marca
✓ INCLUYE el logotipo en la carcasa (acabado tipo espejo)
✓ Funciona como bocina bluetooth estándar — calidad de sonido decente para uso casual

🎵 ESPECIFICACIONES TÉCNICAS
• Conectividad: Bluetooth 5.0 (alcance ~10 m)
• Potencia: 40W RMS aproximada
• Certificación: IP67 (resistente a salpicaduras y polvo)
• Batería: Li-ion recargable, hasta 8 horas de reproducción
• Carga: Cable USB-C incluido
• Auracast / multipunto: NO disponible
• Aplicación móvil: NO compatible

📦 INCLUYE
• 1 bocina bluetooth
• 1 cable de carga USB-C
• 1 manual de uso
• Empaque genérico

🛡️ GARANTÍA
30 días por defectos de fábrica. Cambio físico únicamente.

📋 IDEAL PARA
• Uso recreativo y portátil
• Quien busca un producto similar al original a precio accesible
• Quien NO requiere conectarse a la app oficial de la marca

🚫 NO RECOMENDADO PARA
• Quien busca un producto 100% original
• Quien necesita la app móvil para ecualización
• Audiófilos exigentes

📞 ATENCIÓN AL CLIENTE
Respondemos en horario laboral (10:00 AM – 5:00 PM, hora CDMX) por mensajería de Mercado Libre.

⚠️ Al comprar este producto reconoces que conoces sus características reales y que NO es un producto original de marca."""

print(f"\n=== Aplicando corrección ===")
print(f"Nuevo título: {NEW_TITLE}")

# Update título
r1 = requests.put(f"https://api.mercadolibre.com/items/{ITEM_ID}",
                  headers=H, json={"title": NEW_TITLE}, timeout=20)
print(f"Update título: HTTP {r1.status_code}")
if r1.status_code != 200:
    print(f"  err: {r1.text[:400]}")

# Update descripción
r2 = requests.put(f"https://api.mercadolibre.com/items/{ITEM_ID}/description",
                  headers=H, json={"plain_text": NEW_DESC}, timeout=20)
print(f"Update descripción: HTTP {r2.status_code}")
if r2.status_code != 200:
    print(f"  err: {r2.text[:400]}")

ok = (r1.status_code == 200 and r2.status_code == 200)

if TG and TGCID:
    msg = f"✏️ *Item {ITEM_ID} corregido*\n\n"
    msg += f"Cuenta: {owner_acc}\n"
    msg += f"Status item: {item_data.get('status')}\n\n"
    msg += f"*Nuevo título:*\n{NEW_TITLE}\n\n"
    if ok:
        msg += "✅ Título y descripción actualizados.\n"
        msg += "Mañana al reactivarse aparecerá con el texto nuevo."
    else:
        msg += "⚠️ Hubo errores en la actualización, ver log."
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                  data={"chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=15)

print(f"\n{'✅' if ok else '❌'} Listo")
