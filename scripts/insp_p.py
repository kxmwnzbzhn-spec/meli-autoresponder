import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=15).json(); uid=me.get("id")
for path in [f"/catalog_charts/MLM/domain/MLM-UNDERPANTS",
             f"/catalog_charts/MLM/domain_id/MLM-UNDERPANTS",
             f"/catalog_charts/structure?domain_id=MLM-UNDERPANTS&site_id=MLM",
             f"/users/{uid}/catalog_charts/structure?domain_id=MLM-UNDERPANTS"]:
    try:
        r=requests.get(f"{API}{path}",headers=H,timeout=20)
        print(f"\n### {path} -> {r.status_code}")
        print(r.text[:900])
    except Exception as e: print(path,"EXC",e)
print("DONE")
