import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
a=requests.get(f"{API}/categories/MLM59800/attributes",headers=H,timeout=20).json()
for at in a:
    if at.get("id")=="EMPTY_GTIN_REASON":
        print("EMPTY_GTIN_REASON values:")
        for v in (at.get("values") or []): print("  id=",v.get("id")," name=",v.get("name"))
    if at.get("id")=="GTIN":
        print("GTIN tags:", at.get("tags"))
print("DONE")
