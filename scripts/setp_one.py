import os, requests
import meli_token
IID="MLM2940662359"; PRICE=799
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
b=requests.get(f"{API}/items/{IID}?attributes=id,seller_id,status,price,title",headers=H,timeout=20).json()
print(f"{IID} '{b.get('title','')[:40]}' antes=${b.get('price')} status={b.get('status')}")
r=requests.put(f"{API}/items/{IID}",headers=HJ,json={"price":PRICE},timeout=20)
print(f"set price http={r.status_code}")
f=requests.get(f"{API}/items/{IID}?attributes=price",headers=H,timeout=20).json()
print(f"ahora=${f.get('price')}"); print("DONE")
