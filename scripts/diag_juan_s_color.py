"""Identificar colores reales de los S_Color en Juan via variation_attributes."""
import os, requests
from datetime import datetime, timezone, timedelta
from collections import defaultdict

APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID = me["id"]

date_from = (datetime.now(timezone.utc) - timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

print(f"=== JUAN ({me.get('nickname')}) — analizando Go 4 S/Color ===\n")
color_count = defaultdict(int)
detail = []

offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={date_from}&limit=50&offset={offset}",headers=H,timeout=20).json()
    res = rr.get("results",[])
    if not res: break
    for o in res:
        sh = o.get("shipping",{}) or {}
        sh_id = sh.get("id")
        if not sh_id: continue
        sd = requests.get(f"https://api.mercadolibre.com/shipments/{sh_id}",headers=H,timeout=10).json()
        if sd.get("status") != "ready_to_ship" or sd.get("substatus") != "printed": continue
        
        for oi in o.get("order_items",[]):
            title = (oi.get("item") or {}).get("title","")
            if "go 4" not in title.lower() and "go4" not in title.lower(): continue
            tl = title.lower()
            # Si ya tiene un color en el título, skip (ya se categorizó bien)
            if any(c in tl for c in ["azul","rojo","roja","negr","rosa","camuflaje","camo","aqua","celeste","morad","blanc","verde","amarillo"]):
                continue
            
            # Es S_Color — extraer color real de variation_attributes
            var_attrs = (oi.get("item") or {}).get("variation_attributes") or []
            color_real = "?"
            for a in var_attrs:
                if a.get("id") == "COLOR" or a.get("name","").lower() == "color":
                    color_real = a.get("value_name","?"); break
            
            # También probar variation_id resolviendo
            var_id = (oi.get("item") or {}).get("variation_id")
            
            color_count[color_real] += oi.get("quantity",0)
            detail.append({
                "order": o.get("id"),
                "shipment": sh_id,
                "title": title[:50],
                "color": color_real,
                "var_id": var_id,
                "qty": oi.get("quantity",0),
            })
    offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break

print("=== Resumen colores reales (de variation_attributes) ===")
for c, n in sorted(color_count.items(), key=lambda x: -x[1]):
    print(f"  {c}: {n} u")

print(f"\n=== Detalle por shipment ({len(detail)}) ===")
for d in detail[:30]:
    print(f"  ship={d['shipment']} order={d['order']} qty={d['qty']} color={d['color']} | {d['title']}")
