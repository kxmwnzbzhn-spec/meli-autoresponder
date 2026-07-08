import os, requests, json
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

# Check current item
g=requests.get("https://api.mercadolibre.com/items/MLM3100147427",headers=H,timeout=10).json()
print(f"\n=== MLM3100147427 ===",flush=True)
print(f"  status: {g.get('status')}  cat_id: {g.get('category_id')}",flush=True)
print(f"  title: {g.get('title','?')[:80]}",flush=True)

# Get category info to confirm names
for cat_id in ("MLM1271","MLM456032"):
    c=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}",timeout=10).json()
    path=" > ".join([p.get("name","?") for p in c.get("path_from_root",[])])
    print(f"\n  {cat_id}: {c.get('name','?')}",flush=True)
    print(f"    path: {path}",flush=True)

# Also check what CPID recommends
p=requests.get("https://api.mercadolibre.com/products/MLM75022568",headers=H,timeout=10).json()
print(f"\n  CPID MLM75022568 recommended cat:")
for a in p.get("attributes",[])[:5]:
    if a.get("id")=="ITEM_CATEGORY":
        print(f"    ITEM_CATEGORY: {a.get('value_id')}",flush=True)
        break
# Look for category info in product
print(f"  status: {p.get('status')}  parent: {p.get('parent_id')}",flush=True)

# Try to change category
print(f"\n=== TRY change category to MLM456032 ===",flush=True)
r=requests.put("https://api.mercadolibre.com/items/MLM3100147427",headers=H,
               json={"category_id":"MLM456032"},timeout=15).json()
print(f"  new cat: {r.get('category_id')} err: {r.get('error','')} msg: {r.get('message','')}",flush=True)
if r.get("error"):
    print(f"  cause: {json.dumps(r.get('cause',[]))[:600]}",flush=True)
