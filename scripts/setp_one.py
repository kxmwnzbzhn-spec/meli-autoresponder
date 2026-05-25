import os, requests
import meli_token
JOBS=[("MLM2950839631",1499),("MLM2950801553",1499)]
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
for IID,PRICE in JOBS:
    b=requests.get(f"{API}/items/{IID}?attributes=price,title,status",headers=H,timeout=20).json()
    r=requests.put(f"{API}/items/{IID}",headers=HJ,json={"price":PRICE},timeout=20)
    f=requests.get(f"{API}/items/{IID}?attributes=price",headers=H,timeout=20).json()
    print(f"{IID} '{b.get('title','')[:35]}' {b.get('price')}->{f.get('price')} http={r.status_code}")
print("DONE")
