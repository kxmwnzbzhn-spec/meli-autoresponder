"""Set descriptions usando POST + texto en formato MELI correcto."""
import os, requests, time, json

APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
TOKEN=r["access_token"]
H_json={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

ITEMS = {
    "MLM2894654315": "Negro",
    "MLM2894631211": "Azul",
    "MLM2894618113": "Rojo",
}

def desc(color):
    return f"""JBL CHARGE 6 - REACONDICIONADA - Color {color}

ESTÉTICA 10/10 - Apariencia perfecta, sin marcas ni rayones.

DEFECTOS DECLARADOS - LEA POR FAVOR:
- NO compatible con la aplicación JBL Portable
- NO compatible con Auracast (LE Audio)
- NO compatible con PartyBoost

SOLO funciona conexión Bluetooth básica.

TODO LO DEMÁS FUNCIONA AL 100%:
- Bluetooth 5.3 estable y rápido
- Sonido Original Pro Sound JBL (graves profundos)
- Resistencia agua y polvo IP67 (sumergible)
- Batería de 28 horas de duración
- Powerbank funcional vía USB-C
- Manos libres / Llamadas con micrófono
- Carga rápida USB-C (1.5h carga completa)
- Estructura física PERFECTA - luce como nueva

COLOR: {color}
Autonomía: hasta 28 horas
Potencia: 45 W RMS
Resistencia: IP67 (sumergible 1m por 30min)
Bluetooth: 5.3
Carga: USB-C
Conectividad: SOLO Bluetooth (NO Auracast, NO PartyBoost)

INCLUYE:
- 1 x Bocina JBL Charge 6 ({color})
- 1 x Cable USB-C de carga
- Empaque seguro reforzado

ENVÍO GRATIS en 1 a 3 días hábiles
Garantía 90 días contra defectos de operación

Pregunte ANTES de comprar si tiene dudas.
Las TRES limitaciones son: app JBL, Auracast y PartyBoost.
SOLO conexión Bluetooth básica.
El sonido y demás funciones son IDÉNTICAS al modelo de tienda.

Vendedor MercadoLíder con miles de ventas exitosas.
Compre con total confianza.
"""

for iid, color in ITEMS.items():
    print(f"\n=== {iid} ({color}) ===")
    txt = desc(color)
    
    # Try multiple formats
    attempts = [
        ("POST plain_text", "POST", H_json, json.dumps({"plain_text": txt})),
        ("PUT plain_text", "PUT", H_json, json.dumps({"plain_text": txt})),
        ("POST raw text/plain", "POST", {"Authorization":f"Bearer {TOKEN}","Content-Type":"text/plain;charset=utf-8"}, txt.encode("utf-8")),
        ("POST text", "POST", H_json, json.dumps({"text": txt})),
    ]
    
    for name, method, headers, body in attempts:
        try:
            url = f"https://api.mercadolibre.com/items/{iid}/description"
            if method == "POST":
                rp = requests.post(url, headers=headers, data=body, timeout=30)
            else:
                rp = requests.put(url, headers=headers, data=body, timeout=30)
            print(f"  [{name}] HTTP {rp.status_code}: {rp.text[:200]}")
            
            # Verify
            time.sleep(2)
            rd = requests.get(url, headers={"Authorization":f"Bearer {TOKEN}"}, timeout=15).json()
            saved = rd.get("plain_text","") or rd.get("text","")
            print(f"    saved length: {len(saved)} | preview: '{saved[:80]}'")
            
            if len(saved) > 100:
                print(f"  ✅ {name} funcionó!")
                break
        except Exception as e:
            print(f"  [{name}] err: {e}")
        time.sleep(0.5)
    
    time.sleep(1)
