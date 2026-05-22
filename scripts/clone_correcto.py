"""Clon CORRECTO: catalog_listing=False (como los originales que SÍ ganaban).
Clona MLM2940047227 + cierra los 2 clones forbidden (catalog_listing=True muertos)."""
import os, requests, time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
API="https://api.mercadolibre.com"
T=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT},timeout=15).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# 1) Cerrar los 2 clones forbidden (catalog_listing=True, no sirven)
print("=== Cerrar clones forbidden ===")
for iid in ["MLM5390322498","MLM5390372034"]:
    g=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    print(f"  {iid} status={g.get('status')} sub={g.get('sub_status')}")
    if g.get("status")!="closed":
        if g.get("status")=="active":
            requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"paused"},timeout=15); time.sleep(0.4)
        rc=requests.put(f"{API}/items/{iid}",headers=HJ,json={"status":"closed"},timeout=15)
        print(f"    close http={rc.status_code} {rc.text[:120]}")

# 2) Clonar MLM2940047227 con catalog_listing=FALSE (como original)
print("\n=== CLON 2940047227 catalog_listing=False ===")
g=requests.get(f"{API}/items/MLM2940047227",headers=H,timeout=10).json()
cpid=g.get("catalog_product_id"); cat=g.get("category_id"); price=g.get("price"); title=g.get("title")
pics=[{"id":p.get("id")} for p in (g.get("pictures") or [])]
attrs=[]
for a in (g.get("attributes") or []):
    if a.get("id") in ("BRAND","MODEL","COLOR") and a.get("value_name"):
        attrs.append({"id":a["id"],"value_name":a["value_name"]})
print(f"  origen: '{title[:40]}' cpid={cpid} price=${price}")

payload={"site_id":"MLM","title":title,"category_id":cat,"price":price or 350,"currency_id":"MXN",
    "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro",
    "condition":"new","catalog_product_id":cpid,"catalog_listing":False,
    "pictures":pics,"attributes":attrs}
r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=30)
print(f"  http={r.status_code}")
new_id=None
if r.status_code<300:
    new_id=r.json().get("id"); print(f"  NEW: {new_id} ✅")
    time.sleep(2)
    g2=requests.get(f"{API}/items/{new_id}",headers=H,timeout=10).json()
    print(f"  post: status={g2.get('status')} sub={g2.get('sub_status')}")
    p=requests.get(f"{API}/items/{new_id}/price_to_win?version=v2",headers=H,timeout=10).json()
    print(f"  PTW: {p.get('status')} ptw={p.get('price_to_win')}")
else:
    print(f"  body={r.text[:500]}")
if new_id: print(f"\nNUEVO_ID={new_id} (Go3, floor 349)")
