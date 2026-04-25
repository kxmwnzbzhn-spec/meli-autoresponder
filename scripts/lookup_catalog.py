import os, requests, json, sys
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN","")

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
if r.status_code != 200:
    print("token err", r.status_code, r.text); sys.exit(1)
at = r.json()["access_token"]

cpid = "MLM44710367"
r = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers={"Authorization":f"Bearer {at}"})
print(f"GET /products/{cpid} → {r.status_code}")
if r.status_code != 200:
    print(r.text); sys.exit(1)
p = r.json()
print(json.dumps({
    "id": p.get("id"),
    "name": p.get("name"),
    "domain_id": p.get("domain_id"),
    "category_id": p.get("category_id"),
    "status": p.get("status"),
    "buy_box_winner_price": p.get("buy_box_winner",{}).get("price") if p.get("buy_box_winner") else None,
    "main_features": [mf.get("text","")[:60] for mf in (p.get("main_features") or [])][:3],
    "n_attributes": len(p.get("attributes",[])),
    "pictures_count": len(p.get("pictures") or [])
}, indent=2, ensure_ascii=False))

# get current sellers for buy box price reference
r2 = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=5", headers={"Authorization":f"Bearer {at}"})
if r2.status_code == 200:
    for it in r2.json().get("results",[])[:5]:
        print(f"  competitor item: {it.get('item_id')} ${it.get('price')} stock={it.get('available_quantity')} cond={it.get('condition')} status={it.get('status','')}")
