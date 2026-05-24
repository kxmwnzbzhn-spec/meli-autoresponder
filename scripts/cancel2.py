import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
T=meli_token.refresh(RT).json()["access_token"]
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
sid="MLM5395078678"
tests=[
 ("POST cancel", "post", f"/catalog_suggestions/{sid}/cancel", None),
 ("PUT cancel",  "put",  f"/catalog_suggestions/{sid}/cancel", {}),
 ("POST actions","post", f"/catalog_suggestions/{sid}/actions", {"action":"cancel"}),
 ("PUT DELETED", "put",  f"/catalog_suggestions/{sid}", {"status":"DELETED"}),
 ("PUT CLOSED",  "put",  f"/catalog_suggestions/{sid}", {"status":"CLOSED"}),
 ("PUT action",  "put",  f"/catalog_suggestions/{sid}", {"action":"CANCEL"}),
]
for name,meth,path,body in tests:
    fn=getattr(requests,meth)
    r=fn(f"{API}{path}",headers=HJ,json=body,timeout=25) if body is not None else fn(f"{API}{path}",headers=H,timeout=25)
    print(f"[{name:12}] {meth.upper()} {path.split('/')[-1]:24} -> {r.status_code} {r.text[:90]}")
print("DONE")
