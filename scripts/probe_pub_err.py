import os, requests, json
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_AH={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}

cpid="MLM50661134"  # Armaf Maleka
# Get the catalog product details
pr=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
print(f"\nCPID {cpid}")
print(f"name={pr.get('name')}")
print(f"family_name={pr.get('family_name')}")
print(f"buy_box_winner={pr.get('buy_box_winner')}")
print(f"category_id from product={pr.get('category_id')}")
print(f"domain_id={pr.get('domain_id')}")

# Try with various payloads
bb=pr.get("buy_box_winner") or {}
price=bb.get("price") or 800
cat=None
if bb.get("item_id"):
    tmp=requests.get(f"{API}/items/{bb['item_id']}",headers=H,timeout=10).json()
    cat=tmp.get("category_id")
print(f"buy-box winner category: {cat}")

# Attempt 1: minimal payload (no title)
p1={"site_id":"MLM","category_id":cat or "MLM177562","price":price,"currency_id":"MXN",
   "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new",
   "catalog_product_id":cpid,"catalog_listing":True,
   "shipping":{"mode":"me2","free_shipping":True}}
r1=requests.post(f"{API}/items",headers=HJ,json=p1,timeout=30)
print(f"\nAttempt 1 (no title): {r1.status_code}")
print(json.dumps(r1.json() if r1.headers.get('content-type','').startswith('application/json') else {"text":r1.text},indent=2,ensure_ascii=False)[:1500])

# Attempt 2: with title
p2={**p1,"title":(pr.get('name') or '')[:60]}
r2=requests.post(f"{API}/items",headers=HJ,json=p2,timeout=30)
print(f"\nAttempt 2 (with title): {r2.status_code}")
print(json.dumps(r2.json() if r2.headers.get('content-type','').startswith('application/json') else {"text":r2.text},indent=2,ensure_ascii=False)[:1500])
