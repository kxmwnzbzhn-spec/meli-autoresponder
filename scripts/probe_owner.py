import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
ASVA=me.get("id")
CPID="MLM48919985"

g=requests.get(f"{API}/products/{CPID}",headers=H,timeout=10).json()
print(f"ASVA seller_id: {ASVA}")
print(f"CPID creator_id: {g.get('creator_id')}")
print(f"  match: {g.get('creator_id')==ASVA}")
print(f"  pdp_types: {g.get('pdp_types')}")
print(f"  status: {g.get('status')}")

# Probe edit/PUT endpoints with full enumeration
print("\n=== PROBE EDIT ENDPOINTS ===")
probes=[
  ("PUT",f"{API}/products/{CPID}",{"name":"test"}),
  ("PATCH",f"{API}/products/{CPID}",{"name":"test"}),
  ("POST",f"{API}/products/{CPID}",{"name":"test"}),
  ("POST",f"{API}/catalog/edit_requests",{"product_id":CPID}),
  ("POST",f"{API}/catalog/edits",{"product_id":CPID}),
  ("POST",f"{API}/catalog/products/{CPID}/edits",{}),
  ("POST",f"{API}/catalog_products/{CPID}/edits",{}),
  ("POST",f"{API}/products/{CPID}/edits",{}),
  ("POST",f"{API}/products/{CPID}/update",{}),
  ("POST",f"{API}/users/me/products/{CPID}",{}),
  ("POST",f"{API}/catalog/items",{}),
  ("GET",f"{API}/users/{ASVA}/products",None),
  ("GET",f"{API}/users/{ASVA}/catalog/products",None),
  ("GET",f"{API}/catalog/products?seller_id="+str(ASVA),None),
  ("GET",f"{API}/products/search?seller_id="+str(ASVA),None),
]
for method,url,body in probes:
  try:
    if method=="GET": r=requests.get(url,headers=H,timeout=8)
    else: r=requests.request(method,url,headers=H,json=body,timeout=8)
    suffix=url.split("/")[3:]
    print(f"{method} /{'/'.join(suffix)} -> {r.status_code}: {r.text[:150]}")
  except Exception as e:
    print(f"{method} {url} -> ERR {e}")
