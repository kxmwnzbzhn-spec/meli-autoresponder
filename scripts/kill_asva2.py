import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Tree: top categories
tree=requests.get(f"{API}/sites/MLM/categories",headers=H,timeout=15).json()
print("=== TOP MLM CATS ===")
for t in tree:
  n=(t.get("name") or "").lower()
  if "espir" in n or "esot" in n or "religi" in n or "ocult" in n:
    print(f"  {t['id']} - {t['name']}")

# Try predict from title
for q in ["Perfume esoterico Flor de Nopal","Perfume ritual","Perfume santeria","Lociones esotericas","Locion ritual ataccion"]:
  pr=requests.get(f"{API}/sites/MLM/category_predictor/predict?title={requests.utils.quote(q)}",headers=H,timeout=10)
  print(f"\npredict '{q}': {pr.status_code}", pr.text[:300])

# Walk tree for esoterismo
def walk(cid,depth=0):
  if depth>4: return
  ci=requests.get(f"{API}/categories/{cid}",headers=H,timeout=10).json()
  n=(ci.get("name") or "").lower()
  if "esot" in n or "ritual" in n or "espir" in n or "ocult" in n or "magic" in n:
    print(f"{'  '*depth}{cid} - {ci.get('name')} [LEAF={not ci.get('children_categories')}]")
  for ch in ci.get("children_categories",[]):
    walk(ch["id"],depth+1)

# Probe Belleza y Cuidado (parent of perfumes)
print("\n=== Walking MLM1246 (Belleza) for esoterico ===")
walk("MLM1246")
print("\n=== Walking MLM1431 (Hogar) for esoterico ===")
walk("MLM1431")
