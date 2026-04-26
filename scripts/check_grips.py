import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

ITEMS = [
    "MLM5245746244",
    "MLM5245746252",
    "MLM5245757608",
]

r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}"}

for iid in ITEMS:
    print(f"\n{'='*70}\n=== {iid} ===")
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
    print(f"  catalog_listing: {g.get('catalog_listing')}")
    print(f"  catalog_product_id: {g.get('catalog_product_id')}")
    print(f"  status: {g.get('status')}")
    print(f"  price: ${g.get('price')}")
    print(f"  tags: {g.get('tags',[])}")
    
    # Try the catalog_listing_status endpoint
    try:
        cls = requests.get(f"https://api.mercadolibre.com/items/{iid}/catalog_listing_status",headers=H,timeout=10)
        print(f"  catalog_listing_status: {cls.status_code} → {cls.text[:500]}")
    except Exception as e:
        print(f"  catalog_listing_status ERR: {e}")
    
    # Try competition endpoint
    try:
        cmp = requests.get(f"https://api.mercadolibre.com/items/{iid}/competition",headers=H,timeout=10)
        print(f"  competition: {cmp.status_code} → {cmp.text[:500]}")
    except Exception as e:
        print(f"  competition ERR: {e}")
    
    # Try health endpoint  
    try:
        hth = requests.get(f"https://api.mercadolibre.com/items/{iid}/health",headers=H,timeout=10)
        print(f"  health: {hth.status_code} → {hth.text[:500]}")
    except Exception as e:
        print(f"  health ERR: {e}")
    
    # Catalog product full data
    cpid = g.get('catalog_product_id')
    if cpid:
        p = requests.get(f"https://api.mercadolibre.com/products/{cpid}?include_attributes=all",headers=H,timeout=10).json()
        bbw = p.get("buy_box_winner")
        print(f"  catalog buy_box_winner: {bbw}")
        # Try also the items endpoint with filters
        items = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?status=active&limit=5",headers=H,timeout=10).json()
        print(f"  catalog items returned (top 5):")
        for it in items.get("results",[])[:5]:
            mark = " 👈 NOSOTROS" if it.get("item_id")==iid else ""
            print(f"    {it.get('item_id')} ${it.get('price')} log={(it.get('shipping',{}) or {}).get('logistic_type','')}{mark}")
