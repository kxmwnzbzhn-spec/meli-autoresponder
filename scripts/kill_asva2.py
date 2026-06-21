import os, requests, re
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Known esoteric perfume item from search results
KNOWN="MLM2852170458"
print(f"=== probe {KNOWN} ===")
g=requests.get(f"{API}/items/{KNOWN}?attributes=id,title,category_id,catalog_product_id",headers=H,timeout=15).json()
print(g)
if g.get("category_id"):
  c=g["category_id"]
  ci=requests.get(f"{API}/categories/{c}",headers=H,timeout=10).json()
  print(f"\ncat name: {ci.get('name')}")
  print(f"path: {' > '.join(p.get('name') for p in ci.get('path_from_root',[]))}")
  print(f"children: {len(ci.get('children_categories',[]))}")
  for ch in ci.get("children_categories",[]):
    print(f"  child: {ch['id']} - {ch['name']}")

# Also: walk MLM6111 or wherever esoterismo lives (try various roots)
# Try: GET parent of perfumes esotericos
print("\n=== check tree path from cat ===")
for c in [g.get("category_id")] if g.get("category_id") else []:
  if not c: continue
  parent_id=None
  ci=requests.get(f"{API}/categories/{c}",headers=H,timeout=10).json()
  pfr=ci.get("path_from_root",[])
  if len(pfr)>=2: parent_id=pfr[-2].get("id")
  print(f"parent: {parent_id}")
  if parent_id:
    pi=requests.get(f"{API}/categories/{parent_id}",headers=H,timeout=10).json()
    for ch in pi.get("children_categories",[]):
      print(f"  sibling: {ch['id']} - {ch['name']}")
