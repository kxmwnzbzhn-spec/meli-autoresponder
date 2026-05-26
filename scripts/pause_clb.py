import os, requests
import meli_token
IID="MLM5245310494"; PRICE=499; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
it=requests.get(f"{API}/items/{IID}",headers=H,timeout=20).json()
print(f"{IID} '{(it.get('title') or '')[:40]}' status={it.get('status')} qty={it.get('available_quantity')} price={it.get('price')} vars={len(it.get('variations') or [])}")
# set price
rp=requests.put(f"{API}/items/{IID}",headers=HJ,json={"price":PRICE},timeout=15)
print(f"  price->{PRICE}: {rp.status_code}")
# var qty>=1
vp=[{"id":v.get("id"),"available_quantity":1} for v in (it.get("variations") or []) if (v.get("available_quantity") or 0)<1]
if vp:
    r1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"variations":vp},timeout=15)
    print(f"  var qty: {r1.status_code}")
body={"status":"active"}
if not (it.get("variations") or []) and (it.get("available_quantity") or 0)<1: body["available_quantity"]=1
r2=requests.put(f"{API}/items/{IID}",headers=HJ,json=body,timeout=15)
print(f"  activate: {r2.status_code} {('' if r2.status_code<300 else r2.text[:200])}")
f=requests.get(f"{API}/items/{IID}?attributes=status,price,available_quantity",headers=H,timeout=15).json()
print(f"FINAL status={f.get('status')} price={f.get('price')} qty={f.get('available_quantity')}")
print("DONE")
