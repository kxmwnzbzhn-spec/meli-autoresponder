import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}
print("=== domain_discovery boxers ===")
for q in ["paquete 3 boxers calvin klein","boxers hombre microfibra","calzoncillos boxer hombre","pack boxers hombre","boxer brief hombre"]:
    r=requests.get(f"{API}/sites/MLM/domain_discovery/search",params={"q":q,"limit":4},headers=H,timeout=15)
    print(f"\nq='{q}'")
    try:
        for d in r.json(): print(f"  {d.get('domain_id')} | {d.get('domain_name')} | cat={d.get('category_id')} ({d.get('category_name')})")
    except Exception as e: print("  err",e)
