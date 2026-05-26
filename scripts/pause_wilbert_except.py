import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
cid="5515483546"
for path in [f"/post-purchase/v1/claims/{cid}",
             f"/post-purchase/v2/claims/{cid}",
             f"/v1/claims/{cid}",
             f"/post-purchase/v1/claims/{cid}/players",
             f"/post-purchase/v1/claims/{cid}/expected_resolutions",
             f"/post-purchase/v1/claims/{cid}/actions"]:
    r=requests.get(f"{API}{path}",headers=H,timeout=20)
    print(f"\n### {path} -> {r.status_code} ct={r.headers.get('content-type','')[:30]}")
    print(r.text[:800])
print("DONE")
