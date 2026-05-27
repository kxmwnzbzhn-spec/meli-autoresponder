import os, requests
API="https://api.mercadolibre.com"
def tok(rt):
    return requests.post(f"{API}/oauth/token",data={
        "grant_type":"refresh_token",
        "client_id":os.environ["MELI_APP_ID"],
        "client_secret":os.environ["MELI_APP_SECRET"],
        "refresh_token":rt},timeout=20).json()

ta=tok(os.environ["MELI_REFRESH_TOKEN_ASVA"]); TA=ta["access_token"]
print(f"NEW_RT_ASVA={ta.get('refresh_token')}")
HA={"Authorization":f"Bearer {TA}"}
tm=tok(os.environ["MELI_REFRESH_TOKEN_MAYRELY"]); TM=tm["access_token"]
print(f"NEW_RT_MAYRELY={tm.get('refresh_token')}")
HM={"Authorization":f"Bearer {TM}"}; HJM={**HM,"Content-Type":"application/json"}

SRC="MLM2947607629"
src=requests.get(f"{API}/items/{SRC}",headers=HA,timeout=20).json()
print(f"SRC: {src.get('title')} cat={src.get('category_id')}")

# Generic listing (no GTIN required when BRAND=Genérico + MODEL=Genérico)
title="Auriculares Inalámbricos Bluetooth 5.3 In-ear Color Negro"[:60]
pictures=[{"source":p["secure_url"]} for p in (src.get("pictures") or [])][:10]

# Build attributes: keep only safe ones + add BRAND/MODEL=Genérico
KEEP_ATTRS={"COLOR","PRIMARY_COLOR","CONNECTIVITY","CONNECTION_INTERFACE","HEADPHONE_FORMAT","WITH_MICROPHONE","WITH_NOISE_CANCELLATION","IS_WIRELESS","BLUETOOTH_VERSION","BATTERY_TYPE","BATTERY_DURATION","INCLUDES_CHARGING_BASE","ITEM_CONDITION","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT"}
attrs=[]
for a in (src.get("attributes") or []):
    aid=a.get("id")
    if aid in KEEP_ATTRS and (a.get("value_name") or a.get("value_id")):
        o={"id":aid}
        if a.get("value_id"): o["value_id"]=a["value_id"]
        if a.get("value_name"): o["value_name"]=a["value_name"]
        attrs.append(o)
# Force Generic brand+model to waive GTIN
attrs.append({"id":"BRAND","value_name":"Genérico"})
attrs.append({"id":"MODEL","value_name":"Genérico"})

payload={
    "site_id":"MLM",
    "title":title,
    "category_id":src.get("category_id"),
    "price":src.get("price"),
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_special",
    "condition":"new",
    "description":{"plain_text":"Auriculares Bluetooth in-ear con micrófono integrado. Sonido HD, batería de larga duración, control táctil. Producto nuevo, sellado."},
    "pictures":pictures,
    "attributes":attrs,
    "shipping":{"mode":"me2","free_shipping":False}
}
r=requests.post(f"{API}/items",headers=HJM,json=payload,timeout=40)
print(f"\nPOST: {r.status_code}")
if r.status_code in (200,201):
    d=r.json()
    print(f"NEW ITEM: {d['id']}")
    print(f"  status={d.get('status')}")
    print(f"  price=${d.get('price')}")
    print(f"  title='{d.get('title')[:80]}'")
    print(f"  URL: {d.get('permalink')}")
else:
    print(f"ERROR: {r.text[:800]}")
