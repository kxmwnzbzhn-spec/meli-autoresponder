import os, requests
import meli_token
IID="MLM5346655686"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_WILBERT"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
it=requests.get(f"{API}/items/{IID}",headers=H,timeout=20).json()
print(f"status={it.get('status')} variations={len(it.get('variations') or [])}")
vars_payload=[{"id":v.get("id"),"available_quantity":1} for v in (it.get("variations") or []) if v.get("id")]
if vars_payload:
    r1=requests.put(f"{API}/items/{IID}",headers=HJ,json={"variations":vars_payload},timeout=20)
    print(f"set var qty=1 each -> {r1.status_code} {('' if r1.status_code<300 else r1.text[:300])}")
r2=requests.put(f"{API}/items/{IID}",headers=HJ,json={"status":"active"},timeout=20)
print(f"set status=active -> {r2.status_code} {('' if r2.status_code<300 else r2.text[:300])}")
fin=requests.get(f"{API}/items/{IID}?attributes=status,available_quantity",headers=H,timeout=15).json()
print(f"FINAL status={fin.get('status')} qty={fin.get('available_quantity')}")
print("DONE")
