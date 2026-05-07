"""Corrige título + descripción del item MLM5296392666.
Producto real: réplica calidad 1.1, espejo, NO compatible con app, INCLUYE logo.
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
    "WILBERT":  os.environ.get("MELI_REFRESH_TOKEN_WILBERT"),
    "ASGARI":   os.environ.get("MELI_REFRESH_TOKEN_ASGARI"),
    "ANGEL":    os.environ.get("MELI_REFRESH_TOKEN_ANGEL"),
}

def tok(rt):
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={
        "grant_type":"refresh_token","client_id":APP_ID,
        "client_secret":APP_SECRET,"refresh_token":rt}).json()
    return r.get("access_token")

# Encontrar dueño del item
owner_acc = None
owner_at = None
for acc, rt in ACCS.items():
    if not rt: continue
    at = tok(rt)
    if not at: continue
    me = requests.get("https://api.mercadolibre.com/users/me", headers={"Authorization":f"Bearer {at}"}).json()
    uid = me.get("id")
    item = requests.get(f"https://api.mercadolibre.com/items/{ITEM_ID}", timeout=15).json()
    if item.get("seller_id") == uid:
        owner_acc = acc
        owner_at = at
        print(f"Dueño: {acc} (uid {uid})")
        print(f"Título actual: {item.get('title')}")
        print(f"Status: {item.get('status')}")
        print(f"Price: ${item.get('price')}")
        break

if not owner_at:
    print(f"❌ No encontré quién es dueño de {ITEM_ID}")
    exit(1)

H = {"Authorization": f"Bearer {owner_at}", "Content-Type":"application/json"}

# Bajar descripción actual
desc_r = requests.get(f"https://api.mercadolibre.com/items/{ITEM_ID}/description", headers=H).json()
print(f"\nDescripción actual ({len(desc_r.get('plain_text','') or '')} chars):")
print((desc_r.get("plain_text","") or "")[:500])
print("...")

# Nuevo título profesional (60 chars max)
NEW_TITLE = "Bocina Bluetooth Portátil Inalámbrica Recargable IP67 40W"

# Descripción profesional honesta
NEW_DESC = """🔊 BOCINA BLUETOOTH PORTÁTIL — PRODUCTO COMPATIBLE 1.1

⚠️ INFORMACIÓN IMPORTANTE — Lee antes de comprar
Este producto es una bocina bluetooth REPLICA (calidad 1.1 / espejo) que IMITA el diseño de modelos premium reconocidos. Te lo informamos con total transparencia:

✗ NO es producto original de marca
✗ NO es compatible con la app oficial de la marca
✓ INCLUYE el logotipo en la carcasa (acabado tipo espejo)
✓ Funciona como bocina bluetooth estándar — calidad de sonido decente para uso casual

🎵 ESPECIFICACIONES TÉCNICAS
• Conectividad: Bluetooth 5.0 (alcance ~10 m)
• Potencia: 40W RMS aprox.
• Certificación: IP67 (resistente a salpicaduras y polvo)
• Batería: Recargable Li-ion, hasta 8 horas de reproducción
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
• Quien busca producto 100% original
• Quien necesita la app móvil para ecualización
• Audiófilos exigentes

📞 ATENCIÓN AL CLIENTE
Respondemos en horario laboral (10 AM – 5 PM CDMX) por mensajería de Mercado Libre.

⚠️ Al comprar este producto aceptas que conoces sus características reales y no es un producto original de marca."""

print(f"\n=== Aplicando corrección ===")
print(f"Nuevo título: {NEW_TITLE}")

# Update título
r1 = requests.put(f"https://api.mercadolibre.com/items/{ITEM_ID}",
                  headers=H, json={"title": NEW_TITLE}, timeout=20)
print(f"Update título: HTTP {r1.status_code}")
if r1.status_code != 200:
    print(f"  err: {r1.text[:300]}")

# Update descripción
r2 = requests.put(f"https://api.mercadolibre.com/items/{ITEM_ID}/description",
                  headers=H, json={"plain_text": NEW_DESC}, timeout=20)
print(f"Update descripción: HTTP {r2.status_code}")
if r2.status_code != 200:
    print(f"  err: {r2.text[:300]}")

if TG and TGCID:
    msg = f"✏️ *Corrección aplicada*\n\nItem: `{ITEM_ID}`\nCuenta: {owner_acc}\n\n*Nuevo título:*\n{NEW_TITLE}\n\n_Descripción actualizada con info honesta:_\n• Réplica 1.1 espejo\n• NO compatible con app\n• Incluye logo"
    requests.post(f"https://api.telegram.org/bot{TG}/sendMessage",
                  data={"chat_id":TGCID,"parse_mode":"Markdown","text":msg[:4000]}, timeout=15)

print("\n✅ Listo")
