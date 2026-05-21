"""Clona Redmi Buds (MLM2940664057 de Yiriam) a ASVA:
- Tradicional $399 (sin catalog_listing)
- Catálogo $399 (catalog_product_id=MLM40336571)
ASVA congelado (no hay war de ASVA, queda estático)."""
import os, requests, time
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
RT_A=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"

def tok(rt): return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()["access_token"]

# 1) Leer origen de Yiriam (pics + attributes)
TY=tok(RT_Y)
HY={"Authorization":f"Bearer {TY}"}
g=requests.get(f"{API}/items/MLM2940664057",headers=HY,timeout=10).json()
pics=[{"id":p.get("id")} for p in (g.get("pictures") or [])]
title=g.get("title")
cat=g.get("category_id")  # MLM5072
cpid=g.get("catalog_product_id")  # MLM40336571
print(f"origen: title='{title}' cat={cat} cpid={cpid} pics={len(pics)}")

# Attributes mínimos requeridos (BRAND, MODEL)
attrs=[]
for a in (g.get("attributes") or []):
    if a.get("id") in ("BRAND","MODEL","LINE","COLOR") and a.get("value_name"):
        attrs.append({"id":a["id"],"value_name":a["value_name"]})

# 2) ASVA
TA=tok(RT_A)
HA={"Authorization":f"Bearer {TA}"}
HJA={"Authorization":f"Bearer {TA}","Content-Type":"application/json"}

# 2a) TRADICIONAL $399
trad={
    "site_id":"MLM","title":title,"category_id":cat,"price":399,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
    "condition":"new","pictures":pics,"attributes":attrs,
}
print("\n=== ASVA TRADICIONAL $399 ===")
r=requests.post(f"{API}/items",headers=HJA,json=trad,timeout=30)
print(f"  http={r.status_code}")
if r.status_code<300:
    print(f"  NEW trad: {r.json().get('id')} ✅")
else:
    print(f"  body={r.text[:400]}")

time.sleep(1)
# 2b) CATALOGO $399 (sin title, MELI hereda)
catl={
    "site_id":"MLM","category_id":cat,"price":399,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
    "condition":"new","catalog_product_id":cpid,"catalog_listing":True,
}
print("\n=== ASVA CATALOGO $399 ===")
r2=requests.post(f"{API}/items",headers=HJA,json=catl,timeout=30)
print(f"  http={r2.status_code}")
if r2.status_code<300:
    nid=r2.json().get("id")
    print(f"  NEW catalog: {nid} ✅")
    time.sleep(2)
    pw=requests.get(f"{API}/items/{nid}/price_to_win?version=v2",headers=HA,timeout=10).json()
    print(f"  PTW: {pw.get('status')} ptw={pw.get('price_to_win')}")
else:
    print(f"  body={r2.text[:400]}")
