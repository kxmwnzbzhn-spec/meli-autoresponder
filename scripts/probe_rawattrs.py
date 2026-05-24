import os, requests, json
import meli_token
CPID="MLM52113823"; API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
T=meli_token.refresh(RT).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
p=requests.get(f"{API}/products/{CPID}",headers=H,timeout=20).json()
want={"BRAND","PERFUME_NAME","UNIT_VOLUME","GENDER","MPN","OLFACTORY_NOTES","OLFACTORY_FAMILIES","RELEASE_YEAR"}
for a in (p.get("attributes") or []):
    if a.get("id") in want:
        print(json.dumps(a, ensure_ascii=False))
print("---- top-level product keys ----")
print([k for k in p.keys()])
print("DONE")
