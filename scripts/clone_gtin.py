"""Publicar MLM2940047227 como TRADICIONAL con GTIN, SIN catalog_product_id.
Evita el muro seller.optin.fake. MELI asocia al catálogo automáticamente luego."""
import os, requests, time, json
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

g=requests.get(f"{API}/items/MLM2940047227",headers=H,timeout=10).json()
cat=g.get("category_id"); price=g.get("price"); title=g.get("title")
pics=[{"id":p.get("id")} for p in (g.get("pictures") or [])]
print(f"origen: '{title[:40]}' cat={cat} price=${price}")
# Volcar TODOS los attributes para hallar GTIN/MODEL/BRAND etc
allattrs=g.get("attributes") or []
keep=[]
gtin=None
for a in allattrs:
    aid=a.get("id"); vn=a.get("value_name"); vid=a.get("value_id")
    if aid=="GTIN":
        gtin=vn
    if aid in ("BRAND","MODEL","COLOR","GTIN","LINE","ITEM_CONDITION","EMPACADO_INCLUYE","WIRELESS","WATERPROOF_CAPACITY"):
        if vn:
            keep.append({"id":aid,"value_name":vn})
print(f"GTIN={gtin}")
print(f"attrs keep: {[a['id'] for a in keep]}")

# Descripción del original
desc=""
try:
    d=requests.get(f"{API}/items/MLM2940047227/description",headers=H,timeout=10).json()
    desc=d.get("plain_text","") or ""
except: pass

# Publicar tradicional SIN catalog_product_id
payload={"site_id":"MLM","title":title,"category_id":cat,"price":price or 350,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
    "condition":"new","pictures":pics,"attributes":keep}
print("\n=== Publicar TRADICIONAL sin catalog ===")
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"  http={r.status_code}")
new_id=None
if r.status_code<300:
    new_id=r.json().get("id"); print(f"  NEW: {new_id} ✅ status={r.json().get('status')}")
    if desc:
        time.sleep(1)
        rd=requests.post(f"{API}/items/{new_id}/description",headers=HJ,json={"plain_text":desc},timeout=15)
        print(f"  desc http={rd.status_code}")
else:
    print(f"  body={r.text[:600]}")
if new_id: print(f"\nNUEVO_ID={new_id}")
