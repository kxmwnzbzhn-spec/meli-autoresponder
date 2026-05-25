import os, requests
import meli_token
IID="MLM2940047221"; PRICE=599; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
b=requests.get(f"{API}/items/{IID}?attributes=price,title,status",headers=H,timeout=20).json()
print(f"{IID} '{b.get('title','')[:40]}' antes=${b.get('price')} status={b.get('status')}")
r=requests.put(f"{API}/items/{IID}",headers=HJ,json={"price":PRICE},timeout=20)
print(f"set price http={r.status_code} {('' if r.status_code==200 else r.text[:200])}")
f=requests.get(f"{API}/items/{IID}?attributes=price",headers=H,timeout=20).json()
print(f"ahora=${f.get('price')}"); print("DONE")
