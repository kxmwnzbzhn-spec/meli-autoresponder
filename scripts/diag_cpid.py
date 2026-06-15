import os, requests, json, time
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
for a in range(4):
  r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token",
    "client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
  if r.status_code<500: break
  time.sleep(5)
tk=r.json(); AT=tk["access_token"]
H={"Authorization":f"Bearer {AT}"}
for cpid in ["MLM61262890","MLM48244979","MLM44709174"]:
  print(f"\n=== {cpid} ===")
  cp=requests.get(f"{API}/products/{cpid}",headers=H,timeout=12)
  print(f"  /products HTTP {cp.status_code}")
  if cp.status_code==200:
    j=cp.json()
    print(f"  name: {j.get('name')[:80] if j.get('name') else None}")
    print(f"  category_id: {j.get('category_id')}")
    print(f"  domain_id: {j.get('domain_id')}")
    print(f"  status: {j.get('status')}")
  # Competitors
  r=requests.get(f"{API}/products/{cpid}/items?limit=5",headers=H,timeout=12)
  print(f"  /items HTTP {r.status_code}")
  if r.status_code==200:
    res=r.json().get("results",[])
    print(f"  competitors: {len(res)}")
    for c in res[:3]:
      iid=c.get("item_id") or c.get("id")
      if iid:
        m=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        cat=m.get("category_id")
        gtin=next((a.get("value_name") for a in m.get("attributes",[]) if a.get("id")=="GTIN"),None)
        print(f"    {iid} cat={cat} gtin={gtin}")
  # Catalog domain
  dd=requests.get(f"{API}/sites/MLM/search?catalog_product_id={cpid}&limit=3",headers=H,timeout=12)
  print(f"  /search?catalog HTTP {dd.status_code}")
  if dd.status_code==200:
    res=dd.json().get("results",[])
    for r2 in res[:2]:
      print(f"    seller {r2.get('seller',{}).get('id')} cat={r2.get('category_id')}")
