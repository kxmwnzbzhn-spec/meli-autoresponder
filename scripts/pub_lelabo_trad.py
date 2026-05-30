import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_AH={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}

# Use the catalog product MLM21617901 (Le Labo Santal 33) info for the new tradicional
pr=requests.get(f"{API}/products/MLM21617901",headers=H,timeout=15).json()
# Get pictures from product
pics=pr.get("pictures") or []
pictures=[{"source":p.get("url")} for p in pics if p.get("url")][:10]
if not pictures:
    # Try main_features pictures
    for f in (pr.get("main_features") or []):
        if f.get("metadata",{}).get("img"):
            pictures.append({"source":f["metadata"]["img"]})

# Try tradicional with BRAND=Genérico + EMPTY_GTIN_REASON
title="Le Labo Santal 33 Eau De Parfum 100 ml Unisex"
payload={
    "site_id":"MLM","title":title,
    "category_id":"MLM1271","price":583,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now",
    "listing_type_id":"gold_special","condition":"new",
    "description":{"plain_text":"Perfume original Le Labo Santal 33. Notas: Sándalo, Cardamomo, Iris, Violeta, Cuero, Almizcle. Frasco 100ml unisex. Sellado de fábrica."},
    "pictures":pictures,
    "attributes":[
        {"id":"BRAND","value_name":"Genérico"},
        {"id":"MODEL","value_name":"Santal 33"},
        {"id":"EMPTY_GTIN_REASON","value_name":"Mi producto no es de marca"},
    ],
    "shipping":{"mode":"me2","free_shipping":False}
}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
print(f"\nAttempt 1 (Generic + EMPTY_GTIN_REASON): {r.status_code}")
if r.status_code in (200,201):
    d=r.json()
    print(f"✓ NEW TRADICIONAL: {d['id']} {d.get('status')} ${d.get('price')}")
    print(f"  url={d.get('permalink')}")
else:
    print(f"  ERR: {r.text[:600]}")
    # Try without EMPTY_GTIN_REASON
    del payload["attributes"][-1]
    r2=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
    print(f"\nAttempt 2 (just Generic): {r2.status_code}")
    if r2.status_code in (200,201):
        d=r2.json()
        print(f"✓ NEW TRADICIONAL: {d['id']} {d.get('status')} ${d.get('price')}")
        print(f"  url={d.get('permalink')}")
    else:
        print(f"  ERR: {r2.text[:600]}")
