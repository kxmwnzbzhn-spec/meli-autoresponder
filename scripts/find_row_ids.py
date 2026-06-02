"""Discover row_ids for chart 5915675."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

# 1) Try chart endpoints with the proven 5915675 id (now we know the name format works)
for ep in [
    "/catalog_charts/5915675/rows",
    "/catalog_charts/5915675/rows?seller_id=3417664339",
    "/charts/5915675/rows",
    "/users/3417664339/catalog_charts/5915675/rows",
    "/users/3417664339/catalog_charts/5915675",
    "/catalog_charts?name=5915675",
    "/catalog_charts?seller_id=3417664339",
    "/users/3417664339/catalog_charts",
    "/catalog_charts/5915675?seller_id=3417664339",
]:
    rr=requests.get(f"{API}{ep}",headers=H,timeout=8)
    print(f"  GET {ep} → {rr.status_code}: {rr.text[:500]}")

# 2) Probe publication with SIZE_GRID_ROW_ID name-based per size
PICS=["https://http2.mlstatic.com/D_NQ_NP_743804-MLA106119402584_022026-F.jpg"]
base={
    "title":"Test CK boxer",
    "category_id":"MLM194115",
    "price":799,"currency_id":"MXN","available_quantity":1,
    "buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_special",
    "pictures":[{"source":u} for u in PICS],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
}
print("\n=== Try with SIZE_GRID_ROW_ID by name ===")
for row_val in ["S","M","L","s","Talla S","S - 71-76 cm"]:
    attrs=[
        {"id":"BRAND","value_name":"Calvin Klein"},
        {"id":"MODEL","value_name":"Brief"},
        {"id":"GENDER","value_name":"Hombre"},
        {"id":"COLOR","value_name":"Mixto"},
        {"id":"MALE_UNDERWEAR_TYPE","value_name":"Bóxer"},
        {"id":"SIZE_GRID_ID","value_name":"5915675"},
        {"id":"SIZE_GRID_ROW_ID","value_name":row_val},
    ]
    p=dict(base); p["attributes"]=attrs
    rv=requests.post(f"{API}/items/validate",headers=HJ,json=p,timeout=15)
    print(f"  row='{row_val}': HTTP {rv.status_code}: {rv.text[:400]}")
