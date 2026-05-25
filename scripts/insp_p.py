import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
# atributos categoria
ca=requests.get(f"{API}/categories/MLM194115/attributes",headers=H,timeout=20).json()
for a in ca:
    if a.get("id") in ("SIZE_GRID_ID","SIZE_GRID_ROW_ID","SIZE"):
        print(a.get("id"),"tags=",a.get("tags"),"vals=",[v.get("name") for v in (a.get("values") or [])][:8])
# size charts disponibles para el dominio
for path in ["/catalog_charts/MLM/search?domain_id=MLM-UNDERPANTS",
             "/sites/MLM/sizes/charts?domain_id=MLM-UNDERPANTS",
             "/categories/MLM194115/classifications_attributes"]:
    try:
        r=requests.get(f"{API}{path}",headers=H,timeout=15)
        print(f"\n{path} -> {r.status_code} {r.text[:300]}")
    except Exception as e: print(path,"EXC",e)
print("DONE")
