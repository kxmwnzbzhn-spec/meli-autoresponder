import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Check boxers item's category
b=requests.get(f"{API}/items/MLM2976325463",headers=H,timeout=15).json()
print(f"CK boxers cat: {b.get('category_id')}")
# Walk up to find Calcetines sibling
cat=b.get("category_id")
chain=[]
while cat:
  ci=requests.get(f"{API}/categories/{cat}",headers=H,timeout=10).json()
  chain.append((cat,ci.get("name")))
  parent=(ci.get("path_from_root") or [])
  if parent:
    print(f"path from root for {cat}:")
    for p in parent: print(f"  {p['id']} - {p['name']}")
  break

# Use the parent and look for Calcetines sibling
for c,_ in chain:
  parent_id=requests.get(f"{API}/categories/{c}",headers=H,timeout=10).json().get("path_from_root",[{}])[-2:][0].get("id")
  if parent_id:
    print(f"\nparent of {c}: {parent_id}")
    pc=requests.get(f"{API}/categories/{parent_id}",headers=H,timeout=10).json()
    for child in pc.get("children_categories",[])[:30]:
      print(f"  {child['id']} - {child['name']}")
