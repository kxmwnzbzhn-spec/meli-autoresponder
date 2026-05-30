import os, requests
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_AH={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}

# Read source (the existing catalog listing)
SRC="MLM2956230171"
src=requests.get(f"{API}/items/{SRC}",headers=H,timeout=15).json()
print(f"SOURCE: {SRC} status={src.get('status')} price=${src.get('price')} title={(src.get('title') or '')[:60]}")

# Use catalog product images
pr=requests.get(f"{API}/products/MLM48766151",headers=H,timeout=15).json()
pics_cat=pr.get("pictures") or []
pictures=[{"source":p.get("url")} for p in pics_cat if p.get("url")][:10]
# Fallback to source pictures
if not pictures:
    pictures=[{"source":p["secure_url"]} for p in (src.get("pictures") or [])][:10]
print(f"pictures: {len(pictures)}")

payload={
    "site_id":"MLM",
    "title":"Perfume Lattafa Khamrah Dukhan Edp 100 Ml Para Caballero",
    "category_id":"MLM1271",
    "price": src.get("price") or 539,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_special",
    "condition":"new",
    "description":{"plain_text":"Perfume Lattafa Khamrah Dukhan EDP 100ml. Notas: especiado, dulce, oriental, cardamomo, canela. Frasco original sellado. Envío inmediato."},
    "pictures":pictures,
    "attributes":[
        {"id":"BRAND","value_name":"Genérico"},
        {"id":"MODEL","value_name":"Genérico"},
        {"id":"UNIT_VOLUME","value_name":"100 ml"},
        {"id":"GENDER","value_name":"Hombre"},
        {"id":"PERFUME_NAME","value_name":"Khamrah Dukhan"},
    ],
    "shipping":{"mode":"me2","free_shipping":True}
}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
print(f"\nPOST: {r.status_code}")
if r.status_code in (200,201):
    d=r.json()
    print(f"✓ NEW TRADICIONAL: {d['id']} status={d.get('status')} ${d.get('price')}")
    print(f"  url={d.get('permalink')}")
else:
    import json
    print(f"ERR: {json.dumps(r.json(),indent=2,ensure_ascii=False)[:1500]}")
