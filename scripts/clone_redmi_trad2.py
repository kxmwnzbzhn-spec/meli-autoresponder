"""ASVA tradicional = replicar estructura Yiriam (catalog_product_id + catalog_listing:False + title)"""
import os, requests, time
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
RT_A=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
def tok(rt): return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()["access_token"]

TY=tok(RT_Y); HY={"Authorization":f"Bearer {TY}"}
g=requests.get(f"{API}/items/MLM2940664057",headers=HY,timeout=10).json()
pics=[{"id":p.get("id")} for p in (g.get("pictures") or [])]
title=g.get("title"); cat=g.get("category_id"); cpid=g.get("catalog_product_id")
attrs=[]
for a in (g.get("attributes") or []):
    if a.get("id") in ("BRAND","MODEL","LINE","COLOR") and a.get("value_name"):
        attrs.append({"id":a["id"],"value_name":a["value_name"]})

TA=tok(RT_A); HJA={"Authorization":f"Bearer {TA}","Content-Type":"application/json"}

# Tradicional: replica Yiriam exacto = catalog_product_id + catalog_listing False + title
trad={
    "site_id":"MLM","title":title,"category_id":cat,"price":399,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
    "condition":"new","pictures":pics,"attributes":attrs,
    "catalog_product_id":cpid,"catalog_listing":False,
}
print("=== ASVA TRADICIONAL (catalog_listing=False + title) ===")
r=requests.post(f"{API}/items",headers=HJA,json=trad,timeout=30)
print(f"  http={r.status_code}")
if r.status_code<300:
    print(f"  NEW trad: {r.json().get('id')} ✅")
else:
    print(f"  body={r.text[:400]}")
