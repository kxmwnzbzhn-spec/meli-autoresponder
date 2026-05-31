import os, requests, json
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}

# Use a working catalog item from same product as reference for pictures
pr=requests.get(f"{API}/products/MLM2023522170",headers=H,timeout=15).json()
pics=pr.get("pictures") or []
pictures=[{"source":p.get("url")} for p in pics if p.get("url")][:10]
if not pictures:
    # Fallback to MLM25912333 (same product different catalog)
    pr2=requests.get(f"{API}/products/MLM25912333",headers=H,timeout=15).json()
    pictures=[{"source":p.get("url")} for p in (pr2.get("pictures") or []) if p.get("url")][:10]

payload={
    "site_id":"MLM",
    "title":"Sony SRS-XB100 Altavoz Bluetooth Negro Caja Abierta",
    "category_id":"MLM59800","price":699,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now",
    "listing_type_id":"gold_special","condition":"new",
    "description":{"plain_text":"Sony SRS-XB100 Bocina Bluetooth Portátil. Nueva con caja abierta solo para inspección. Sellado interno intacto. Hasta 16h batería, IP67 waterproof, sonido grave EXTRA BASS. Envío inmediato."},
    "pictures":pictures,
    "attributes":[
        {"id":"BRAND","value_name":"Genérico"},
        {"id":"MODEL","value_name":"Genérico"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"},
    ],
    "shipping":{"mode":"me2","free_shipping":True}
}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
print(f"\nPOST: {r.status_code}")
if r.status_code in (200,201):
    d=r.json()
    print(f"✓ NEW TRADICIONAL: {d['id']} {d.get('status')} ${d.get('price')}")
    print(f"  url={d.get('permalink')}")
else:
    print(f"ERR: {json.dumps(r.json(),indent=2,ensure_ascii=False)[:1500]}")
