"""V3: probar título alternativo + sin title (catálogo hereda)"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

ATTEMPTS=[
  ("title=brand+model", {"title":"The Alchemia Lab Dark Oud Cacao Edp 100 Ml Unisex"}),
  ("title=product_name_short", {"title":"Perfume The Alchemia Lab Dark Oud Cacao 100 Ml Unisex"}),
  ("title=cat_name_only", {"title":"Perfume Dark Oud Cacao"}),
]

base_payload={
    "site_id":"MLM",
    "category_id":"MLM1271",
    "price":798,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_pro",
    "condition":"new",
    "catalog_product_id":"MLM69794803",
    "catalog_listing":True,
}

for label, extra in ATTEMPTS:
    payload={**base_payload, **extra}
    print(f"\n=== {label}: title='{payload.get('title','-')}' ===")
    r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
    print(f"  http={r.status_code}")
    if r.status_code<300:
        new_id=r.json().get("id")
        print(f"  NEW: {new_id} ✅")
        time.sleep(2)
        pw=requests.get(f"{API}/items/{new_id}/price_to_win?version=v2",headers=H,timeout=10).json()
        print(f"  PTW: {pw.get('status')} ptw={pw.get('price_to_win')}")
        break
    else:
        print(f"  body={r.text[:400]}")
    time.sleep(1)
