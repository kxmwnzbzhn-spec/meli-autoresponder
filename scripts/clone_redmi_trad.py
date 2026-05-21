"""Retry ASVA tradicional con family_name. Confirmar ASVA catalog frozen + Yiriam gana."""
import os, requests, time
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
RT_A=os.environ["MELI_REFRESH_TOKEN_ASVA"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
def tok(rt): return requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()["access_token"]

TY=tok(RT_Y); HY={"Authorization":f"Bearer {TY}"}
g=requests.get(f"{API}/items/MLM2940664057",headers=HY,timeout=10).json()
pics=[{"id":p.get("id")} for p in (g.get("pictures") or [])]
title=g.get("title"); cat=g.get("category_id")
attrs=[]
for a in (g.get("attributes") or []):
    if a.get("id") in ("BRAND","MODEL","LINE","COLOR") and a.get("value_name"):
        attrs.append({"id":a["id"],"value_name":a["value_name"]})

TA=tok(RT_A); HJA={"Authorization":f"Bearer {TA}","Content-Type":"application/json"}; HA={"Authorization":f"Bearer {TA}"}

# Intentos con family_name
for fam in ["Redmi Buds 4 Lite","Buds 4 Lite"]:
    trad={
        "site_id":"MLM","title":title,"category_id":cat,"price":399,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
        "condition":"new","pictures":pics,
        "family_name":fam,
        "attributes":attrs+[{"id":"FAMILY_NAME","value_name":fam}],
    }
    print(f"=== TRADICIONAL family='{fam}' ===")
    r=requests.post(f"{API}/items",headers=HJA,json=trad,timeout=30)
    print(f"  http={r.status_code}")
    if r.status_code<300:
        print(f"  NEW trad: {r.json().get('id')} ✅"); break
    else:
        print(f"  body={r.text[:300]}")
    time.sleep(1)

# Confirmar ASVA catalog frozen + estado
print("\n=== ASVA catalog MLM2947607629 ===")
gc=requests.get(f"{API}/items/MLM2947607629",headers=HA,timeout=10).json()
print(f"  price=${gc.get('price')} status={gc.get('status')}")
pw=requests.get(f"{API}/items/MLM2947607629/price_to_win?version=v2",headers=HA,timeout=10).json()
print(f"  PTW: {pw.get('status')} ptw={pw.get('price_to_win')}")

# Confirmar Yiriam estado catalog
print("\n=== Yiriam MLM2940664057 ===")
gy=requests.get(f"{API}/items/MLM2940664057",headers=HY,timeout=10).json()
print(f"  price=${gy.get('price')} status={gy.get('status')} catalog_listing={gy.get('catalog_listing')}")
pwy=requests.get(f"{API}/items/MLM2940664057/price_to_win?version=v2",headers=HY,timeout=10).json()
print(f"  PTW: {pwy.get('status')} ptw={pwy.get('price_to_win')}")
