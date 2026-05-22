import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# Estado de los 3 clones creados
print("=== Estado clones recientes ===")
for iid in ["MLM5390322498","MLM5390372034","MLM5390346898"]:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    sub=g.get("sub_status")
    print(f"  {iid}: status={g.get('status')} sub={sub} price=${g.get('price')} cpid={g.get('catalog_product_id')} health={g.get('health')}")
    if g.get("status")=="active":
        p=requests.get(f"{API}/items/{iid}/price_to_win?version=v2",headers=H,timeout=10).json()
        print(f"    PTW: {p.get('status')}")

# Reintentar clon de 2940047227 con error visible
print("\n=== Reintento CLON MLM2940047227 ===")
g=requests.get(f"{API}/items/MLM2940047227",headers=H,timeout=10).json()
cpid=g.get("catalog_product_id"); cat=g.get("category_id"); price=g.get("price"); title=g.get("title")
# atributos minimos
attrs=[]
for a in (g.get("attributes") or []):
    if a.get("id") in ("BRAND","MODEL","LINE") and a.get("value_name"):
        attrs.append({"id":a["id"],"value_name":a["value_name"]})
payload={"site_id":"MLM","category_id":cat,"price":price or 350,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
    "condition":"new","catalog_product_id":cpid,"catalog_listing":True,"title":title,"attributes":attrs}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"  http={r.status_code}")
if r.status_code<300:
    print(f"  NEW: {r.json().get('id')} ✅")
else:
    print(f"  body={r.text[:500]}")
