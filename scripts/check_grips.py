import os, requests, json
APP_ID = os.environ["MELI_APP_ID"]; APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]

ITEMS = [
    ("MLM5245746244", "MLM62279317", "Grip IP68 14h"),
    ("MLM5245746252", "MLM61631985", "Grip waterproof"),
    ("MLM5245757608", "MLM59802579", "Grip con luz $999 lock"),
]

r = requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H = {"Authorization":f"Bearer {r['access_token']}"}

for iid, cpid, label in ITEMS:
    print(f"\n{'='*70}\n=== {iid} | {label} ===")
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=10).json()
    print(f"  status: {g.get('status')}")
    print(f"  price: ${g.get('price')}")
    print(f"  qty: {g.get('available_quantity')}")
    print(f"  free_shipping: {g.get('shipping',{}).get('free_shipping')}")
    print(f"  logistic_type: {g.get('shipping',{}).get('logistic_type')}")
    
    # Competition
    print(f"\n  Catálogo {cpid} — competencia:")
    p = requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=10).json()
    bbw = p.get("buy_box_winner") or {}
    print(f"  buy_box_winner: {bbw.get('item_id','-')} ${bbw.get('price','-')}")
    
    r2 = requests.get(f"https://api.mercadolibre.com/products/{cpid}/items?limit=10",headers=H,timeout=10).json()
    for c in (r2.get("results",[]) or [])[:8]:
        is_us = " 👈 NOSOTROS" if c.get("item_id") == iid else ""
        log = (c.get("shipping",{}) or {}).get("logistic_type","")
        print(f"    {c.get('item_id')} ${c.get('price')} log={log}{is_us}")
