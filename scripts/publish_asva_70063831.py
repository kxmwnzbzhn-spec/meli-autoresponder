import os, requests, time
import meli_token

CPID = "MLM70063831"
PRICE = 798
API = "https://api.mercadolibre.com"

RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
H = {"Authorization": f"Bearer {T}"}
HJ = {"Authorization": f"Bearer {T}", "Content-Type": "application/json"}

p = requests.get(f"{API}/products/{CPID}", headers=H, timeout=15).json()
print(f"Product {CPID}: '{p.get('name')}' domain={p.get('domain_id')} status={p.get('status')}")

# derivar category_id: del producto si lo trae, si no de un competidor
cat = p.get("category_id")
pi = requests.get(f"{API}/products/{CPID}/items?limit=10", headers=H, timeout=15).json()
results = pi.get("results") or []
print(f"Competidores ({len(results)}):")
for r in sorted(results, key=lambda x: x.get('price') or 99999)[:8]:
    print(f"  {r.get('item_id') or r.get('id'):<14} ${r.get('price')} sold={r.get('sold_quantity',0)}")
if not cat and results:
    comp = results[0].get("item_id") or results[0].get("id")
    if comp:
        ci = requests.get(f"{API}/items/{comp}?attributes=category_id", headers=H, timeout=15).json()
        cat = ci.get("category_id")
if not cat:
    dd = requests.get(f"{API}/sites/MLM/domain_discovery/search",
                      params={"limit": 1, "q": (p.get("name") or "")[:60]}, headers=H, timeout=15).json()
    if isinstance(dd, list) and dd:
        cat = dd[0].get("category_id")
    print(f"domain_discovery -> category={cat} domain={dd[0].get('domain_id') if isinstance(dd,list) and dd else None}")
print(f"category_id = {cat}")
if not cat:
    print("ABORT: no pude derivar category_id"); raise SystemExit(1)

payload = {
    "site_id": "MLM", "price": PRICE, "currency_id": "MXN",
    "available_quantity": 1, "buying_mode": "buy_it_now",
    "listing_type_id": "gold_pro", "condition": "new",
    "catalog_product_id": CPID, "catalog_listing": True,
}
if cat:
    payload["category_id"] = cat

print(f"\nPublicando ASVA @${PRICE} ...")
r = requests.post(f"{API}/items", headers=HJ, json=payload, timeout=30)
print(f"  http={r.status_code}")
if r.status_code < 300:
    new_id = r.json().get("id")
    print(f"  NEW: {new_id} status={r.json().get('status')} ✅")
    time.sleep(2)
    pw = requests.get(f"{API}/items/{new_id}/price_to_win?version=v2", headers=H, timeout=10).json()
    print(f"  PTW: status={pw.get('status')} ptw={pw.get('price_to_win')} current={pw.get('current_price')}")
else:
    # reintento sin category_id por si MELI la infiere
    if cat:
        payload.pop("category_id", None)
        r2 = requests.post(f"{API}/items", headers=HJ, json=payload, timeout=30)
        print(f"  retry sin category http={r2.status_code}")
        if r2.status_code < 300:
            print(f"  NEW: {r2.json().get('id')} ✅")
        else:
            print(f"  body={r2.text[:600]}")
    else:
        print(f"  body={r.text[:600]}")
print("DONE")
