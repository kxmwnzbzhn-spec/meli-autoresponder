"""Try publishing in MLM194115 with different SIZE attribute configurations to bypass grid."""
import os, requests, json, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]; print(f"NEW_RT_ADRIAN={r.get('refresh_token')}")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}

PICS=[
  "https://http2.mlstatic.com/D_NQ_NP_743804-MLA106119402584_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_958202-MLA106740502843_022026-F.jpg",
  "https://http2.mlstatic.com/D_NQ_NP_890097-MLA106741215883_022026-F.jpg",
]
base={
    "title":"Calvin Klein Pack 3 Boxers Microfibra Hombre Premium",
    "category_id":"MLM194115",
    "price":799,
    "currency_id":"MXN",
    "buying_mode":"buy_it_now",
    "condition":"new",
    "listing_type_id":"gold_special",
    "pictures":[{"source":u} for u in PICS],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":False},
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"}
    ],
}

# T1: no SIZE at all
payload=dict(base)
payload["available_quantity"]=3
payload["attributes"]=[
    {"id":"BRAND","value_name":"Calvin Klein"},
    {"id":"MODEL","value_name":"Brief"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"COLOR","value_name":"Mixto"},
    {"id":"MALE_UNDERWEAR_TYPE","value_name":"Bóxer"},
]
print("\n=== T1: no SIZE attr at all ===")
rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=15)
print(f"  HTTP {rv.status_code}: {rv.text[:400]}")

# T2: SIZE=Único (talla única)
payload=dict(base)
payload["available_quantity"]=3
payload["attributes"]=[
    {"id":"BRAND","value_name":"Calvin Klein"},
    {"id":"MODEL","value_name":"Brief"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"COLOR","value_name":"Mixto"},
    {"id":"MALE_UNDERWEAR_TYPE","value_name":"Bóxer"},
    {"id":"SIZE","value_name":"Único"},
]
print("\n=== T2: SIZE=Único ===")
rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=15)
print(f"  HTTP {rv.status_code}: {rv.text[:400]}")

# T3: with FILTRABLE_SIZE only
payload=dict(base)
payload["available_quantity"]=3
payload["attributes"]=[
    {"id":"BRAND","value_name":"Calvin Klein"},
    {"id":"MODEL","value_name":"Brief"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"COLOR","value_name":"Mixto"},
    {"id":"MALE_UNDERWEAR_TYPE","value_name":"Bóxer"},
    {"id":"FILTRABLE_SIZE","value_name":"M"},
]
print("\n=== T3: FILTRABLE_SIZE=M (no SIZE) ===")
rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=15)
print(f"  HTTP {rv.status_code}: {rv.text[:400]}")

# T4: SIZE=L (only one talla) — single item
payload=dict(base)
payload["available_quantity"]=1
payload["title"]="Calvin Klein Pack 3 Boxers Microfibra Hombre Talla L"
payload["attributes"]=[
    {"id":"BRAND","value_name":"Calvin Klein"},
    {"id":"MODEL","value_name":"Brief"},
    {"id":"GENDER","value_name":"Hombre"},
    {"id":"COLOR","value_name":"Mixto"},
    {"id":"MALE_UNDERWEAR_TYPE","value_name":"Bóxer"},
    {"id":"SIZE","value_name":"L"},
]
print("\n=== T4: SIZE=L single ===")
rv=requests.post(f"{API}/items/validate",headers=HJ,json=payload,timeout=15)
print(f"  HTTP {rv.status_code}: {rv.text[:400]}")
