import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]

# Try as CPID first
r1=requests.get(f"{API}/products/MLM2950839631",timeout=15)
print(f"as CPID: {r1.status_code}")
if r1.status_code==200:
  print(json.dumps(r1.json(),indent=2,ensure_ascii=False)[:1500])

# Try as item across all tokens
print("\nas ITEM probe across accounts...")
ACC={"AH":"MELI_REFRESH_TOKEN_AH","ASVA":"MELI_REFRESH_TOKEN_ASVA","CLARIBEL":"MELI_REFRESH_TOKEN_CLARIBEL","WILBERT":"MELI_REFRESH_TOKEN_WILBERT","JUAN":"MELI_REFRESH_TOKEN_JUAN","RAYMUNDO":"MELI_REFRESH_TOKEN_RAYMUNDO","YC_NEW":"MELI_REFRESH_TOKEN_YC_NEW"}
for a,k in ACC.items():
  rt=os.environ.get(k)
  if not rt: continue
  try:
    tr=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":rt},timeout=20)
    if tr.status_code>=400: continue
    AT=tr.json()["access_token"]
    g=requests.get(f"{API}/items/MLM2950839631?attributes=id,title,price,status,seller_id,catalog_product_id,category_id",
                   headers={"Authorization":f"Bearer {AT}"},timeout=15)
    if g.status_code==200:
      print(f"  ✓ accessible via {a}: {g.json()}")
      break
    else:
      print(f"  ✗ {a}: HTTP {g.status_code}")
  except Exception as e: print(f"  {a} err: {e}")
