"""Check buy box winner for each Raymundo catalog item."""
import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r = requests.post("https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me = requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
USER_ID = me["id"]
print(f"Cuenta: {me.get('nickname')} ({USER_ID})\n")

# Get ALL active catalog items
ids = []
offset = 0
while True:
    rr = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    b = rr.get("results",[])
    if not b: break
    ids.extend(b); offset += 50
    if offset >= rr.get("paging",{}).get("total",0): break

print(f"Items active: {len(ids)}\n")

losing = []
winning = []
no_competitors = []

for iid in ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,price,catalog_listing,catalog_product_id,status,available_quantity",headers=H,timeout=10).json()
    if not g.get("catalog_listing"): continue
    cpid = g.get("catalog_product_id")
    title = g.get("title","")[:55]
    price = g.get("price")
    qty = g.get("available_quantity")
    if not cpid:
        print(f"  ❓ NO CPID {iid} ({title}) — skipping")
        continue
    
    # Get items in the catalog product
    items_rr = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=20",headers=H,timeout=15).json()
    results = items_rr.get("results",[]) if isinstance(items_rr, dict) else []
    
    # Get buy_box_winner
    pr = requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
    bbw = pr.get("buy_box_winner") or {}
    bb_price = bbw.get("price")
    bb_seller = bbw.get("seller_id")
    
    # Find competitors (excluding our items)
    our_ids = set([iid])
    competitors = [r for r in results if r.get("item_id") not in our_ids]
    cheapest_competitor = min((r.get("price") for r in competitors if r.get("price")),default=None)
    
    is_winner = bb_seller == USER_ID
    icon = "🏆" if is_winner else ("❌" if cheapest_competitor and cheapest_competitor < price else "⚠️")
    
    line = f"  {icon} {iid} ${price} | bb_winner={'WE' if is_winner else bb_seller} bb_price=${bb_price} | comp_min=${cheapest_competitor} qty={qty} | {title}"
    print(line)
    
    if is_winner:
        winning.append((iid, price))
    elif cheapest_competitor:
        losing.append({"iid":iid,"price":price,"cpid":cpid,"comp_min":cheapest_competitor,"bb":bb_price,"title":title})
    else:
        no_competitors.append((iid,price))

print(f"\n=== RESUMEN ===")
print(f"🏆 Ganando: {len(winning)}")
print(f"❌ Perdiendo: {len(losing)}")
print(f"❓ Sin competidor visible: {len(no_competitors)}")

if losing:
    print(f"\n=== ITEMS PERDIENDO ===")
    for l in losing:
        gap = l['comp_min'] - l['price']
        print(f"  {l['iid']} ${l['price']} (comp ${l['comp_min']}, bb ${l['bb']}, gap ${gap}) | {l['title']}")
