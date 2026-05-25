import os, requests
import meli_token
IID="MLM2950790151"; EXP=3364413125; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
it=requests.get(f"{API}/items/{IID}?attributes=seller_id,status,title",headers=H,timeout=20).json()
print(f"{IID} '{(it.get('title') or '')[:40]}' status={it.get('status')} seller={it.get('seller_id')}")
if it.get("seller_id")==EXP:
    if it.get("status")=="active": print("pause:",requests.put(f"{API}/items/{IID}",headers=HJ,json={'status':'paused'},timeout=20).status_code)
    print("close:",requests.put(f"{API}/items/{IID}",headers=HJ,json={'status':'closed'},timeout=20).status_code)
    print("delete:",requests.put(f"{API}/items/{IID}",headers=HJ,json={'deleted':'true'},timeout=20).status_code)
else: print("SKIP no Yiriam")
print("DONE")
