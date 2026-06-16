import os, requests
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
HJ={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}

IID="MLM5517827340"
g=requests.get(f"{API}/items/{IID}?attributes=id,title,price,status,catalog_product_id,catalog_listing",headers=H,timeout=15).json()
print(f"PRE: {g}")
if (g.get("price") or 0) < 999:
  p=requests.put(f"{API}/items/{IID}",headers=HJ,json={"price":999},timeout=20)
  print(f"PUT 999: {p.status_code} {p.text[:300]}")
g2=requests.get(f"{API}/items/{IID}?attributes=id,title,price,status,catalog_product_id",headers=H,timeout=15).json()
print(f"POST: {g2}")
