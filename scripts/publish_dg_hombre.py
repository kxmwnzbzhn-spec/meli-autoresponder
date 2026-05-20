import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

START_PRICE=988

payload={
    "site_id":"MLM",
    "title":"Dolce & Gabbana Devotion Edp 100 Ml Para Hombre",
    "category_id":"MLM1271",
    "price":START_PRICE,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_pro",
    "condition":"new",
    "catalog_product_id":"MLM47767674",
    "catalog_listing":True,
}

print(f"=== Publicando MLM47767674 a ${START_PRICE} ===")
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"  http={r.status_code}")
if r.status_code<300:
    new_id=r.json().get("id")
    print(f"  NEW: {new_id}")
    time.sleep(2)
    p=requests.get(f"{API}/items/{new_id}/price_to_win?version=v2",headers=H,timeout=10).json()
    print(f"  PTW: {p.get('status')} ptw={p.get('price_to_win')}")
else:
    print(f"  body={r.text[:600]}")
