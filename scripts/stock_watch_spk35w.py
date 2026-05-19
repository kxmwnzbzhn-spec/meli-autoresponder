"""
Stock watcher para SPK35W variantes.
Si ROJO qty=0, marca alerta. Si MORADO qty<5, marca alerta.
Corre cada 30 min via cron.
"""
import os, requests, json
from datetime import datetime

tok = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type": "refresh_token",
    "client_id": os.environ["MELI_APP_ID"],
    "client_secret": os.environ["MELI_APP_SECRET"],
    "refresh_token": os.environ["MELI_REFRESH_TOKEN_USER1668"]
}, timeout=20).json()
h = {"Authorization": f"Bearer {tok['access_token']}"}

CURRENT = "MLM2886030837"  # Rojo
FALLBACK = "MLM2886136351"  # Morado

variants = {
    "ROJO":    "MLM2886030837",
    "MORADO":  "MLM2886136351",
    "AZUL":    "MLM5233454100",
    "NEGRO":   "MLM5233480022"
}

print(f"=== Stock Watch @ {datetime.now().isoformat()[:19]} ===")
for color, mid in variants.items():
    r = requests.get(f"https://api.mercadolibre.com/items/{mid}?attributes=id,price,available_quantity,sold_quantity,status", headers=h, timeout=15).json()
    badge = " 🚨" if (mid == CURRENT and r.get('available_quantity', 0) == 0) else ""
    badge += " ⚠️" if (mid == CURRENT and r.get('available_quantity', 0) <= 3) else ""
    print(f"  {color:<8} ({mid}) | status:{r.get('status'):<10} | qty:{r.get('available_quantity'):<3} | sold:{r.get('sold_quantity'):<3} | ${r.get('price')}{badge}")

# Alerta si rojo qty=0
rojo_data = requests.get(f"https://api.mercadolibre.com/items/{CURRENT}", headers=h, timeout=15).json()
if rojo_data.get('available_quantity', 0) == 0 and rojo_data.get('status') == 'paused':
    print(f"\n🚨🚨🚨 ROJO AGOTADO — TRIGGER SWITCH TO MORADO 🚨🚨🚨")
    print(f"Acciones manuales requeridas:")
    print(f"  1. Update landing sonixmx.com.mx → link al MORADO")
    print(f"  2. Update workflow CAPI whitelist: ROJO→MORADO")
    print(f"  3. Update product photos en landing")
    print(f"  4. Compradores 30d audience sigue válida")
elif rojo_data.get('available_quantity', 0) <= 3:
    print(f"\n⚠️ ROJO bajo stock ({rojo_data.get('available_quantity')}). Prepararse para switch.")
else:
    print(f"\n✓ Rojo stock OK: {rojo_data.get('available_quantity')}")




