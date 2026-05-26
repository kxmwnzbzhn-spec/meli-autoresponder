import os, requests
import meli_token
IID="MLM2911241921"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_WILBERT"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
it=requests.get(f"{API}/items/{IID}",headers=H,timeout=20).json()
print(f"{IID} '{(it.get('title') or '')[:50]}' status={it.get('status')} qty={it.get('available_quantity')} vars={len(it.get('variations') or [])}")
vars_payload=[]
for v in (it.get("variations") or []):
    cq=v.get("available_quantity") or 0
    if cq<1: vars_payload.append({"id":v.get("id"),"available_quantity":1})
if vars_payload:
    r1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"variations":vars_payload},timeout=20)
    print(f"set var qty=1 ({len(vars_payload)} var) -> {r1.status_code} {('' if r1.status_code<300 else r1.text[:300])}")
body={"status":"active"}
if not (it.get("variations") or []) and (it.get("available_quantity") or 0)<1:
    body["available_quantity"]=1
r2=requests.put(f"{API}/items/{IID}",headers=HJ,json=body,timeout=20)
print(f"set status=active -> {r2.status_code} {('' if r2.status_code<300 else r2.text[:300])}")
fin=requests.get(f"{API}/items/{IID}?attributes=status,available_quantity,price",headers=H,timeout=15).json()
print(f"FINAL status={fin.get('status')} qty={fin.get('available_quantity')} price={fin.get('price')}")
print("DONE")
