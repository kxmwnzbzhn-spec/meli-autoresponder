"""Quick diag: count active vs paused Raymundo + last sale time."""
import os, requests
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
USER_ID = me["id"]

active=[]; paused=[]
for st in ("active","paused"):
    offset = 0
    while True:
        rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=50&offset={offset}",headers=H,timeout=15).json()
        b = rr.get("results",[])
        if not b: break
        if st=="active": active.extend(b)
        else: paused.extend(b)
        offset += 50
        if offset >= rr.get("paging",{}).get("total",0): break

print(f"=== RAYMUNDO ({me.get('nickname')}) ===")
print(f"  Active: {len(active)}")
print(f"  Paused: {len(paused)}")

# Multi-get to see qty/catalog status of all
all_ids = active + paused
items = {}
for i in range(0, len(all_ids), 20):
    chunk = ",".join(all_ids[i:i+20])
    rr = requests.get(f"https://api.mercadolibre.com/items?ids={chunk}&attributes=id,title,status,available_quantity,catalog_listing,price",headers=H,timeout=20).json()
    for it in rr:
        if it.get("code")==200: items[it["body"]["id"]] = it["body"]

print("\n=== Detalle ===")
for iid, b in items.items():
    title = (b.get("title") or "")[:40]
    qty = b.get("available_quantity")
    st = b.get("status")
    cat = "📦" if b.get("catalog_listing") else "📄"
    icon = "🟢" if st=="active" else "🔴"
    print(f"  {icon} {cat} {iid} ({st}, qty={qty}, ${b.get('price')}) | {title}")

# Check today's sales
import datetime
midnight = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=6)).replace(hour=0,minute=0,second=0,microsecond=0).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
sales=0; offset=0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.date_created.from={midnight}&limit=50&offset={offset}",headers=H,timeout=20).json()
    res = rr.get("results",[])
    if not res: break
    for o in res:
        if o.get("status") in ("paid","shipped","delivered"):
            for oi in o.get("order_items",[]): sales += oi.get("quantity",0)
    offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break
print(f"\nVentas hoy CDMX: {sales}")
