import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json().get("access_token")
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

CPID="MLM40336571"
PRICE=299

# Get product details
pd=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H).json()
title=pd.get("name","Auriculares Xiaomi Redmi Buds 4 Lite Bluetooth 5.3 In-ear Negro")
pics=[(p.get("url") or p.get("secure_url")) for p in (pd.get("pictures") or [])][:8]
attrs={a.get("id"):a.get("value_name") for a in (pd.get("attributes") or [])}
print(f"Catalog: {title}")
print(f"  domain={pd.get('domain_id')}")
print(f"  attrs sample: BRAND={attrs.get('BRAND')} MODEL={attrs.get('MODEL')} COLOR={attrs.get('COLOR')}")
# Detect category
cat_id="MLM1000"  # Audio (will fall back), but let me use the catalog suggestion
# Actually the category for headphones is MLM1276 (Audífonos)
cat_id="MLM1276"

# === Catalog listing ===
print("\n--- 1) Catalog listing ---")
body_cat={
    "title":title,
    "category_id":cat_id,
    "catalog_listing":True,
    "catalog_product_id":CPID,
    "price":PRICE,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_pro",
    "condition":"new",
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"}
    ]
}
r1=requests.post("https://api.mercadolibre.com/items",headers=HJ,json=body_cat)
print(f"POST http={r1.status_code}")
new_cat=None
if r1.status_code<300:
    new_cat=r1.json().get("id")
    print(f"  ✓ CATALOG NEW_ID={new_cat} ${r1.json().get('price')}")
else:
    print(f"  ✗ {r1.text[:400]}")

time.sleep(1.5)

# === Tradicional (NO catalog) ===
print("\n--- 2) Tradicional listing ---")
# Upload pics for tradicional
def upload_pic(t,u):
    img=requests.get(u,timeout=20)
    if img.status_code!=200: return None
    files={"file":("p.jpg",img.content,"image/jpeg")}
    r=requests.post("https://api.mercadolibre.com/pictures/items/upload",headers={"Authorization":f"Bearer {t}"},files=files)
    return r.json().get("id") if r.status_code<300 else None

pic_ids=[]
for u in pics[:6]:
    pid=upload_pic(T,u)
    if pid: pic_ids.append(pid)
print(f"  uploaded {len(pic_ids)} pics")

title_trad="Auriculares Bluetooth In Ear Inalambricos Audifonos Manos Libres"[:60]
body_trad={
    "title":title_trad,
    "category_id":cat_id,
    "price":PRICE,
    "currency_id":"MXN",
    "available_quantity":1,
    "buying_mode":"buy_it_now",
    "listing_type_id":"gold_pro",
    "condition":"new",
    "pictures":[{"id":p} for p in pic_ids] if pic_ids else None,
    "attributes":[
        {"id":"BRAND","value_name":"Genérica"},
        {"id":"MODEL","value_name":"BT-LITE"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"}
    ],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"drop_off"},
    "sale_terms":[
        {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
        {"id":"WARRANTY_TIME","value_name":"30 días"}
    ]
}
if body_trad["pictures"] is None: body_trad.pop("pictures")
r2=requests.post("https://api.mercadolibre.com/items",headers=HJ,json=body_trad)
print(f"POST http={r2.status_code}")
new_trad=None
if r2.status_code<300:
    new_trad=r2.json().get("id")
    print(f"  ✓ TRAD NEW_ID={new_trad} ${r2.json().get('price')}")
else:
    print(f"  ✗ {r2.text[:500]}")

print(f"\n=== SUMMARY ===")
print(f"  Catalog: {new_cat}")
print(f"  Tradicional: {new_trad}")
