import os, requests, json
APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN"]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
}).json()
H = {"Authorization":f"Bearer {r['access_token']}"}

# Search products for JBL Go 4 — multiple variants
all_products = {}

queries = [
    "JBL Go 4",
    "JBL GO4",
    "Bocina JBL Go 4",
    "Parlante JBL Go 4",
    "Altavoz JBL Go 4",
]

for q in queries:
    r = requests.get(
        f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={q.replace(' ','+')}&limit=50",
        headers=H, timeout=15
    ).json()
    for p in r.get("results", []):
        pid = p.get("id")
        name = (p.get("name") or "").strip()
        # Filter only Go 4 (not Go 3, Go 2, Go Essential, Pro, Squad Edition, etc)
        nl = name.lower()
        if not ("go 4" in nl or "go4" in nl):
            continue
        # Skip Go 4 Pro / Pro models (different SKUs)
        if "pro" in nl:
            continue
        # Skip cases / cubiertas / accesorios
        skip_words = ["case", "cubierta", "funda", "carcasa", "estuche", "estuche", "soporte", "cable"]
        if any(sw in nl for sw in skip_words):
            continue
        if pid not in all_products:
            all_products[pid] = {
                "id": pid,
                "name": name,
                "domain_id": p.get("domain_id",""),
                "main_features": [(mf.get("text") or "")[:80] for mf in (p.get("main_features") or [])][:2]
            }

print(f"Total catálogos JBL Go 4 únicos: {len(all_products)}\n")
for pid, info in sorted(all_products.items()):
    print(f"  {pid}: {info['name']}")
    if info.get('domain_id'):
        print(f"    domain: {info['domain_id']}")
    if info.get('main_features'):
        print(f"    features: {' | '.join(info['main_features'])}")
    print()
