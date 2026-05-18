import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json().get("access_token")
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

CPID="MLM40336571"; PRICE=299; CAT="MLM5072"
pd=requests.get(f"https://api.mercadolibre.com/products/{CPID}",headers=H).json()
title=pd.get("name","")
pics=[(p.get("url") or p.get("secure_url")) for p in (pd.get("pictures") or [])][:8]
print(f"title: {title[:65]}")

# 1) Catalog
print("\n--- 1) CATALOG ---")
body_cat={
    "title":title,"category_id":CAT,"catalog_listing":True,"catalog_product_id":CPID,
    "price":PRICE,"currency_id":"MXN","available_quantity":1,"buying_mode":"buy_it_now",
    "listing_type_id":"gold_pro","condition":"new",
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}]
}
r1=requests.post("https://api.mercadolibre.com/items",headers=HJ,json=body_cat)
print(f"POST http={r1.status_code}")
new_cat=None
if r1.status_code<300:
    new_cat=r1.json().get("id")
    print(f"  ✓ NEW_ID={new_cat} ${r1.json().get('price')}")
else:
    print(f"  ✗ {r1.text[:500]}")
time.sleep(1.5)

# 2) Tradicional con pics
print("\n--- 2) TRADICIONAL ---")
def upload(t,u):
    img=requests.get(u,timeout=20)
    if img.status_code!=200: return None
    files={"file":("p.jpg",img.content,"image/jpeg")}
    r=requests.post("https://api.mercadolibre.com/pictures/items/upload",headers={"Authorization":f"Bearer {t}"},files=files)
    return r.json().get("id") if r.status_code<300 else None

pic_ids=[]
for u in pics[:6]:
    pid=upload(T,u)
    if pid: pic_ids.append(pid)
print(f"  pics uploaded: {len(pic_ids)}")

title_trad="Audífonos Bluetooth In Ear Inalámbricos Manos Libres Negro"[:60]
body_trad={
    "title":title_trad,"category_id":CAT,"price":PRICE,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new",
    "pictures":[{"id":p} for p in pic_ids],
    "attributes":[
        {"id":"BRAND","value_name":"Genérica"},
        {"id":"MODEL","value_name":"BT-LITE-IE"},
        {"id":"ITEM_CONDITION","value_name":"Nuevo"}
    ],
    "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"drop_off"},
    "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}]
}
r2=requests.post("https://api.mercadolibre.com/items",headers=HJ,json=body_trad)
print(f"POST http={r2.status_code}")
new_trad=None
if r2.status_code<300:
    new_trad=r2.json().get("id")
    print(f"  ✓ NEW_ID={new_trad} ${r2.json().get('price')}")
else:
    print(f"  ✗ {r2.text[:600]}")

print(f"\n=== SUMMARY ===\n  Catalog: {new_cat}\n  Tradicional: {new_trad}")
