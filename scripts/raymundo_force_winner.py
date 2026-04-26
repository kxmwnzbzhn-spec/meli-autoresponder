"""
RAYMUNDO FORCE WINNER
=====================
Para CADA item catálogo de Raymundo:
1. Consultar /items/{iid}/price_to_win → MELI te dice EXACTAMENTE el precio para ganar BB
2. Si retorna current_price > target → bajar al target
3. Aplicar ese precio (con floor de seguridad)
"""
import os, requests, json, time

APP_ID = os.environ["MELI_APP_ID"]
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]

FLOOR_DEFAULT = 299  # nunca bajar de aquí salvo override
FLOORS = {
    # JBL Grip
    "MLM2891178657": 999, "MLM2891189903": 999,
    # Sony XB100
    "MLM2891178511": 599,
}

r = requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]
print(f"Cuenta: {me.get('nickname')} ({USER_ID})\n")

ids = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break

print(f"Items active: {len(ids)}\n")
adjusted = 0; already_winning = 0; errors = 0; no_data = 0

for iid in ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,catalog_listing,catalog_product_id,status",headers=H,timeout=10).json()
    if not g.get("catalog_listing"): continue
    title = (g.get("title") or "")[:50]
    price = g.get("price")
    cpid = g.get("catalog_product_id")
    
    # /items/{id}/price_to_win — official MELI endpoint
    p = requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win",headers=H,timeout=15)
    if p.status_code != 200:
        no_data += 1
        print(f"  ❓ {iid} ${price} | no price_to_win (HTTP {p.status_code}) | {title}")
        continue
    
    d = p.json()
    status = d.get("status")  # "winning" / "competing" / "sharing_first_place"
    price_to_win = d.get("price_to_win")
    current_price = d.get("current_price")
    
    floor = FLOORS.get(iid, FLOOR_DEFAULT)
    
    if status == "winning":
        already_winning += 1
        print(f"  🏆 {iid} ${price} | WINNING (current=${current_price}) | {title}")
        continue
    
    # Necesitamos bajar precio
    if price_to_win is None:
        no_data += 1
        print(f"  ❓ {iid} ${price} | status={status} sin price_to_win | {title}")
        continue
    
    target = max(floor, price_to_win - 1)  # 1 peso menos que price_to_win, respetando floor
    
    if abs(price - target) < 1:
        already_winning += 1
        print(f"  ✓ {iid} ${price} ya en target ${target} (status={status}) | {title}")
        continue
    
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=H,json={"price": target},timeout=15)
    if rp.status_code == 200:
        adjusted += 1
        print(f"  💰 {iid} ${price} → ${target} (status era {status}, ptw={price_to_win}) | {title}")
    else:
        errors += 1
        print(f"  ❌ {iid} ${price} → ${target} FALLÓ {rp.status_code}: {rp.text[:120]}")
    time.sleep(0.2)

print(f"\n=== RESUMEN ===")
print(f"💰 Ajustados: {adjusted}")
print(f"🏆 Ya ganando: {already_winning}")
print(f"❓ Sin datos: {no_data}")
print(f"❌ Errores: {errors}")
