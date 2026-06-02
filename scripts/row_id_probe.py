"""Probe row_id formats for chart 5915675."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

PICS=["https://http2.mlstatic.com/D_NQ_NP_743804-MLA106119402584_022026-F.jpg"]
base={
    "title":"Test CK boxer",
    "category_id":"MLM194115",
    "price":799,"currency_id":"MXN","available_quantity":1,
    "buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_special",
    "pictures":[{"source":u} for u in PICS],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
}
common=[
    {"id":"BRAND","value_name":"Calvin Klein"},
    {"id":"MODEL","value_name":"Brief"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"COLOR","value_name":"Mixto"},
    {"id":"MALE_UNDERWEAR_TYPE","value_name":"Bóxer"},
    {"id":"SIZE_GRID_ID","value_name":"5915675"},
    {"id":"SIZE","value_name":"S"},
]

# 1) Test without ROW_ID — see if SIZE_GRID_ID alone + SIZE works
print("=== T1: SIZE_GRID_ID + SIZE only (no ROW_ID) ===")
p=dict(base); p["attributes"]=common
rv=requests.post(f"{API}/items/validate",headers=HJ,json=p,timeout=15)
print(f"  HTTP {rv.status_code}: {rv.text[:500]}")

# 2) Try numeric row_ids (chart is 5915675 — rows may be sequential)
print("\n=== T2: Try numeric row_ids ===")
for rid in ["1","2","3","100","5915675","5915676","5915677"]:
    p=dict(base); p["attributes"]=common+[{"id":"SIZE_GRID_ROW_ID","value_id":rid}]
    rv=requests.post(f"{API}/items/validate",headers=HJ,json=p,timeout=15)
    err=""
    try:
        j=rv.json()
        cause=j.get("cause",[{}])[0] if isinstance(j.get("cause"),list) else {}
        err=cause.get("code","")
    except: err=rv.text[:60]
    print(f"  row_id={rid}: HTTP {rv.status_code}: {err}")

# 3) Try row_id with value_name=numeric strings
print("\n=== T3: SIZE_GRID_ROW_ID value_name as int strings ===")
for rid in ["1","2","3"]:
    p=dict(base); p["attributes"]=common+[{"id":"SIZE_GRID_ROW_ID","value_name":rid}]
    rv=requests.post(f"{API}/items/validate",headers=HJ,json=p,timeout=15)
    print(f"  value_name={rid}: HTTP {rv.status_code}: {rv.text[:200]}")

# 4) MELI may have a /catalog_charts/charts/{id}/items endpoint to look up rows
print("\n=== T4: GET deeper chart paths ===")
for ep in [
    "/catalog_charts/charts/5915675",
    "/catalog_charts/charts?seller_id=3417664339",
    "/seller/3417664339/charts",
    "/seller/3417664339/catalog_charts",
    "/catalog/charts/5915675",
]:
    rr=requests.get(f"{API}{ep}",headers=H,timeout=8)
    print(f"  {ep} → {rr.status_code}: {rr.text[:200]}")
