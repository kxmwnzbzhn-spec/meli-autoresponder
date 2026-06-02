"""Probe to find the correct SIZE_GRID_ID format for chart 5915675."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
uid=me.get("id"); print(f"seller={uid}")

# Check Adrián recent items — maybe the test he published has the real chart_id
print("\n=== Adrián's most recent items ===")
recent=requests.get(f"{API}/users/{uid}/items/search?orders=date_created_desc&limit=20",headers=H,timeout=15).json()
ids=recent.get("results") or []
print(f"Total recent: {len(ids)}")
for iid in ids[:10]:
    g=requests.get(f"{API}/items/{iid}?attributes=id,title,category_id,attributes",headers=H,timeout=10).json()
    sgi=next(((a.get("value_id"),a.get("value_name")) for a in (g.get("attributes") or []) if a.get("id")=="SIZE_GRID_ID"),None)
    cat=g.get("category_id")
    ttl=(g.get("title") or "")[:55]
    print(f"  {iid} | cat={cat} | {ttl} | SIZE_GRID_ID={sgi}")

# Also try various GET variations on the chart endpoint
print("\n=== GET chart 5915675 variations ===")
for ep in [
    "/catalog_charts/5915675",
    "/charts/5915675",
    f"/users/{uid}/charts/5915675",
    "/sites/MLM/charts/5915675",
    "/catalog_domains/MLM-UNDERPANTS/charts/5915675",
    "/grids/5915675",
    f"/catalog_charts?id=5915675&site_id=MLM",
]:
    rr=requests.get(f"{API}{ep}",headers=H,timeout=8)
    print(f"  {ep} → {rr.status_code}: {rr.text[:200]}")

# Try POSTing with diff value formats
print("\n=== Try SIZE_GRID_ID format variations ===")
PICS=["https://http2.mlstatic.com/D_NQ_NP_743804-MLA106119402584_022026-F.jpg"]
base={
    "title":"Test CK boxer",
    "category_id":"MLM194115",
    "price":799,"currency_id":"MXN","available_quantity":1,
    "buying_mode":"buy_it_now","condition":"new","listing_type_id":"gold_special",
    "pictures":[{"source":u} for u in PICS],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
}
common_attrs=[
    {"id":"BRAND","value_name":"Calvin Klein"},
    {"id":"MODEL","value_name":"Brief"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"COLOR","value_name":"Mixto"},
    {"id":"MALE_UNDERWEAR_TYPE","value_name":"Bóxer"},
    {"id":"SIZE","value_name":"M"},
]
formats=[
    ("value_id_str_5915675", [{"id":"SIZE_GRID_ID","value_id":"5915675"}]),
    ("value_id_int_5915675", [{"id":"SIZE_GRID_ID","value_id":5915675}]),
    ("value_name_5915675", [{"id":"SIZE_GRID_ID","value_name":"5915675"}]),
    ("with_MLM_prefix", [{"id":"SIZE_GRID_ID","value_id":"MLM5915675"}]),
    ("values_array", [{"id":"SIZE_GRID_ID","values":[{"id":"5915675"}]}]),
    ("values_name_array", [{"id":"SIZE_GRID_ID","values":[{"name":"5915675"}]}]),
]
for name, sgi_attr in formats:
    p=dict(base); p["attributes"]=common_attrs+sgi_attr
    rv=requests.post(f"{API}/items/validate",headers=HJ,json=p,timeout=15)
    print(f"  {name}: HTTP {rv.status_code}: {rv.text[:300]}")
