import os,requests,json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

# Try site search by catalog_product_id
for cpid in ["MLM44715070","MLM68969359","MLM44731934"]:
  print(f"\n=== {cpid} via site search ===")
  url=f"{API}/sites/MLM/search?catalog_product_id={cpid}&limit=50"
  r=requests.get(url,headers=H,timeout=15)
  print(f"  HTTP {r.status_code}")
  if r.status_code==200:
    d=r.json()
    res=d.get("results",[])
    print(f"  results: {len(res)}, paging total: {d.get('paging',{}).get('total')}")
    tot=0
    for it in res[:50]:
      sq=it.get("sold_quantity",0) or 0
      tot+=sq
    print(f"  sum sold_quantity (this page): {tot}")
    if res: 
      sample=res[0]
      print(f"  sample keys: {[k for k in sample.keys() if 'sold' in k.lower() or 'qty' in k.lower() or 'available' in k.lower()]}")
      print(f"  sample seller: {sample.get('seller',{}).get('nickname')} sold={sample.get('sold_quantity')}")

# Try /items by catalog
print("\n=== /products/{cpid}/items deep inspection ===")
it=requests.get(f"{API}/products/MLM44715070/items?limit=10",headers=H,timeout=15).json()
print(json.dumps(it,indent=2,default=str)[:3000])
