"""Retry: usar category predictor para encontrar categoría correcta"""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# Predictor
title="Perfume Dark Oud Cacao The Alchemia Lab Eau De Parfum 100ml"
cp=requests.get(f"{API}/sites/MLM/category_predictor/predict",headers=H,params={"title":title},timeout=10).json()
print(f"Predicted: {cp.get('id')} '{cp.get('name')}'")
cat_id=cp.get("id") or "MLM1271"

payload={
    "site_id":"MLM",
    "title":title[:60],
    "category_id":cat_id,
    "price":798,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_pro",
    "condition":"new",
    "catalog_product_id":"MLM69794803",
    "catalog_listing":True,
}
print(f"\nPublicando a $798 cat={cat_id}")
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"  http={r.status_code}")
if r.status_code<300:
    new_id=r.json().get("id")
    print(f"  NEW: {new_id}")
    time.sleep(2)
    pw=requests.get(f"{API}/items/{new_id}/price_to_win?version=v2",headers=H,timeout=10).json()
    print(f"  PTW: {pw.get('status')} ptw={pw.get('price_to_win')}")
else:
    print(f"  body={r.text[:600]}")
