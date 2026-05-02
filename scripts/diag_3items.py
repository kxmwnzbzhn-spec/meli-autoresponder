import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}"}

ITEMS = ["MLM2891178657", "MLM2891178563", "MLM2891178603"]
for iid in ITEMS:
    print(f"\n=== {iid} ===")
    item = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=10).json()
    print(f"  Title:     {item.get('title','')[:70]}")
    print(f"  Price:     ${item.get('price')}")
    print(f"  Status:    {item.get('status')}/{item.get('sub_status')}")
    print(f"  CPID:      {item.get('catalog_product_id')}")
    cpid = item.get("catalog_product_id")
    if not cpid:
        print("  ⚠️ Sin CPID — no participa en catalog war")
        continue

    # Llamar price_to_win
    try:
        ptw = requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2", headers=H, timeout=10).json()
        print(f"  price_to_win: {json.dumps(ptw, indent=2, ensure_ascii=False)[:600]}")
    except Exception as e:
        print(f"  price_to_win err: {e}")

    # Top competidores en el catálogo
    try:
        prods = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=5", headers=H, timeout=10).json()
        if prods.get("results"):
            print(f"  TOP 5 en catálogo:")
            for p in prods["results"][:5]:
                marker = "👑 NOSOTROS" if p.get("item_id") == iid else ""
                print(f"    ${p.get('price'):>8} {p.get('item_id')} {marker} cond={p.get('condition')} ship={(p.get('shipping') or {}).get('mode')}")
    except Exception as e:
        print(f"  prods err: {e}")
