import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}

CPID="MLM63973616"
pr=requests.get(f"{API}/products/{CPID}",headers=H,timeout=20).json()
title=(pr.get("name") or "")[:60]
print(f"product name: {pr.get('name')}")
print(f"title (max 60): {title}")

payload={
    "site_id":"MLM","title":title,
    "category_id":"MLM59800",  # JBL Go 4 / bocinas
    "price":449,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now",
    "listing_type_id":"gold_pro","condition":"new",
    "catalog_product_id":CPID,"catalog_listing":True,
    "shipping":{"mode":"me2","free_shipping":True},
    "attributes":[{"id":"SELLER_SKU","value_name":"ELEC-027"}]
}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
print(f"POST: {r.status_code}")
if r.status_code in (200,201):
    d=r.json()
    print(f"NEW: {d['id']} status={d.get('status')} price=${d.get('price')} title='{d.get('title')[:70]}'")
    print(f"URL: {d.get('permalink')}")
else:
    print(f"FAIL: {r.text[:800]}")
