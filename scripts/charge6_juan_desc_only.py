"""Solo actualizar descripción Charge 6 (formatos varios)."""
import os, requests, time, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
TOKEN=r["access_token"]

ITEMS = {
    "MLM2894615677": "Negro",
    "MLM2894615713": "Azul",
    "MLM5252530944": "Rojo",
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
    txt = desc(color)
    
    # Variants
    attempts = [
        ("PUT json plain_text", "PUT", {"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}, json.dumps({"plain_text": txt})),
        ("PUT json text", "PUT", {"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}, json.dumps({"text": txt})),
        ("PUT text/plain raw", "PUT", {"Authorization":f"Bearer {TOKEN}","Content-Type":"text/plain;charset=utf-8"}, txt.encode("utf-8")),
        ("POST json plain_text", "POST", {"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}, json.dumps({"plain_text": txt})),
    ]
    
    success = False
    for name, method, headers, body in attempts:
        try:
            if method == "PUT":
                rp = requests.put(f"https://api.mercadolibre.com/items/{iid}/description", headers=headers, data=body, timeout=30)
            else:
                rp = requests.post(f"https://api.mercadolibre.com/items/{iid}/description", headers=headers, data=body, timeout=30)
            print(f"  [{name}] HTTP {rp.status_code}: {rp.text[:200] if rp.status_code not in (200,201) else 'OK'}")
            if rp.status_code in (200, 201):
                success = True
                break
        except Exception as e:
            print(f"  [{name}] err: {e}")
        time.sleep(0.5)
    
    if not success:
        print(f"  ❌ Todos los intentos fallaron")
    time.sleep(1)
