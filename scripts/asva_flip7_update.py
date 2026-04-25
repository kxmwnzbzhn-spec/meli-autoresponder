import os, requests, json, sys, time
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN_ASVA","")

NEW_PRICE = 199.0

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

me = requests.get("https://api.mercadolibre.com/users/me", headers=H).json()
USER_ID = me["id"]
print(f"Cuenta: {me.get('nickname')} ({USER_ID})\n")

# Search all items (active + paused) for Flip 7
all_ids = set()
for st in ["active", "paused"]:
    offset = 0
    while True:
        r = requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={st}&limit=50&offset={offset}", headers=H).json()
        batch = r.get("results", [])
        if not batch: break
        all_ids.update(batch)
        offset += 50
        total = r.get("paging",{}).get("total",0)
        if offset >= total: break

print(f"Items totales (active+paused): {len(all_ids)}\n")

flip7_items = []
print("=== Listado completo ===")
for iid in all_ids:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    title = g.get("title","")
    status = g.get("status","")
    price = g.get("price")
    free = g.get("shipping",{}).get("free_shipping")
    print(f"  {iid} [{status}] ${price} free={free} '{title[:70]}'")
    if "flip 7" in title.lower() or "flip7" in title.lower():
        flip7_items.append(g)

print(f"\nFlip 7 items: {len(flip7_items)}\n")

for it in flip7_items:
    iid = it["id"]
    title = it.get("title","")[:50]
    cur_price = it.get("price")
    status = it.get("status","")
    cur_free = it.get("shipping",{}).get("free_shipping")
    
    print(f"  {iid} [{status}] '{title}'")
    
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                     json={"price": NEW_PRICE})
    print(f"    price ${cur_price} → ${NEW_PRICE} ({rp.status_code})")
    if rp.status_code != 200:
        print(f"      ❌ {rp.text[:300]}")
    
    if cur_free:
        rs = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                         json={"shipping": {"mode": "me2", "free_shipping": False, "tags": ["self_service_in"]}})
        print(f"    free_shipping {cur_free} → False ({rs.status_code})")
        if rs.status_code != 200:
            print(f"      ❌ {rs.text[:300]}")
    else:
        print(f"    free_shipping ya era {cur_free}")
    time.sleep(1)
print("\nDone")
