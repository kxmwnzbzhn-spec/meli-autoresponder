import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
for q in ["Paquete 3 boxers Calvin Klein microfibra","lote 3 boxers","paquete calzones boxer"]:
    dd=requests.get(f"{API}/sites/MLM/domain_discovery/search",params={"limit":8,"q":q},headers=H,timeout=15).json()
    print(f"\nQ={q}")
    for d in (dd if isinstance(dd,list) else []):
        print("  cat=",d.get("category_id")," dom=",d.get("domain_id")," ",d.get("category_name"))
print("DONE")
