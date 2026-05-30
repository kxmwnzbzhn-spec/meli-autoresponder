import os, requests, json
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_AH={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}

pr=requests.get(f"{API}/products/MLM21617901",headers=H,timeout=15).json()
pics=pr.get("pictures") or []
pictures=[{"source":p.get("url")} for p in pics if p.get("url")][:10]

payload={
    "site_id":"MLM",
    "title":"Le Labo Santal 33 Eau De Parfum 100 ml Unisex",
    "category_id":"MLM1271","price":583,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now",
    "listing_type_id":"gold_special","condition":"new",
    "description":{"plain_text":"Perfume original Le Labo Santal 33. Notas: Sándalo, Cardamomo, Iris, Violeta, Cuero, Almizcle. Frasco 100ml unisex. Sellado de fábrica."},
    "pictures":pictures,
    "attributes":[
        {"id":"BRAND","value_name":"Genérico"},
        {"id":"MODEL","value_name":"Genérico"},
        {"id":"UNIT_VOLUME","value_name":"100 ml"},
        {"id":"GENDER","value_name":"Sin género"},
        {"id":"PERFUME_NAME","value_name":"Santal 33"}],
    "shipping":{"mode":"me2","free_shipping":True}}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
print(f"POST: {r.status_code}")
if r.status_code in (200,201):
    d=r.json()
    print(f"✓ NEW TRADICIONAL: {d['id']} {d.get('status')} ${d.get('price')}")
    print(f"  url={d.get('permalink')}")
else:
    print(f"ERR full: {json.dumps(r.json(),indent=2,ensure_ascii=False)[:2000]}")
