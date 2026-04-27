"""Optimizar SEO + agregar defectos a las 3 Charge 6 de Juan."""
import os, requests, time

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

ITEMS = {
    "MLM2894615677": "Negro",
    "MLM2894615713": "Azul",
    "MLM5252530944": "Rojo",
}

# Títulos SEO optimizados (max 60 chars MELI)
SEO_TITLES = {
    "Negro": "Bocina Jbl Charge 6 Bluetooth Ip67 Portatil 28hrs Negra",
    "Azul":  "Bocina Jbl Charge 6 Bluetooth Ip67 Portatil 28hrs Azul",
    "Rojo":  "Bocina Jbl Charge 6 Bluetooth Ip67 Portatil 28hrs Roja",
}

def desc(color):
    return f"""═══════════════════════════════════════
JBL CHARGE 6 — REACONDICIONADA — Color {color}
═══════════════════════════════════════

🌟 ESTÉTICA 10/10 — Apariencia PERFECTA, sin marcas ni rayones 🌟

⚠️ POR FAVOR LEA — DEFECTOS DECLARADOS ⚠️

Este equipo es REACONDICIONADO con SOLO 2 limitaciones:

❌ NO compatible con la aplicación JBL Portable
❌ NO compatible con Auracast (LE Audio)

✅ TODO LO DEMÁS FUNCIONA AL 100%:
  ✓ Bluetooth 5.3 estable y rápido
  ✓ Sonido Original Pro Sound JBL (graves profundos)
  ✓ Resistencia agua y polvo IP67 (sumergible)
  ✓ Batería de 28 horas de duración
  ✓ Powerbank funcional vía USB-C (carga otros dispositivos)
  ✓ PartyBoost (conecta con otras JBL compatibles)
  ✓ Manos libres / Llamadas con micrófono
  ✓ Carga rápida USB-C (1.5h carga completa)
  ✓ Estructura física PERFECTA — luce como nueva

🎨 COLOR: {color}
🔋 Autonomía: hasta 28 horas
🔊 Potencia: 45 W RMS
💧 Resistencia: IP67 (sumergible 1m por 30min)
📶 Bluetooth: 5.3
🔌 Carga: USB-C
🎵 Conectividad: PartyBoost (NO Auracast)

📦 INCLUYE:
  • 1 x Bocina JBL Charge 6 ({color})
  • 1 x Cable USB-C de carga
  • Empaque seguro reforzado

🚚 ENVÍO GRATIS en 1 a 3 días hábiles
🛡️ Garantía 90 días contra defectos de operación

❓ ¿LE INTERESA?
   Pregunte ANTES de comprar si tiene dudas.
   Las DOS únicas limitaciones son la app JBL y Auracast.
   El sonido, calidad de audio y todas las demás funciones
   son IDÉNTICAS al modelo de tienda.

🏆 Vendedor MercadoLíder con miles de ventas exitosas.
   Compre con total confianza.
"""

for iid, color in ITEMS.items():
    print(f"\n=== {iid} ({color}) ===")
    
    # 1) Title
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",
        headers=H, json={"title": SEO_TITLES[color]}, timeout=20)
    print(f"  title PUT {rp.status_code}: {rp.text[:200] if rp.status_code != 200 else SEO_TITLES[color]}")
    
    # 2) Description
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}/description",
        headers=H, json={"plain_text": desc(color)}, timeout=20)
    print(f"  desc PUT {rp.status_code}")
    if rp.status_code not in (200, 201):
        print(f"    {rp.text[:200]}")
    time.sleep(1)

print("\n✅ Listo")
