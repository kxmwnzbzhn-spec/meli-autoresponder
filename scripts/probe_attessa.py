import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}
def sec(t): print(f"\n=== {t} ===")
# producto de referencia (probable 403 WAF)
sec("GET /products/MLMU3530297918")
r=requests.get(f"{API}/products/MLMU3530297918",headers=H,timeout=20)
print("status",r.status_code, r.text[:120] if r.status_code!=200 else "OK")
if r.status_code==200:
    d=r.json(); print("name:",d.get("name"),"| domain:",d.get("domain_id"))
# domain_discovery del tipo de producto
sec("domain_discovery sets/ropa deportiva")
for q in ["set deportivo mujer seamless","conjunto deportivo mujer","ropa deportiva set","conjunto seamless"]:
    rr=requests.get(f"{API}/sites/MLM/domain_discovery/search",params={"q":q,"limit":4},headers=H,timeout=15)
    print(f"\nq='{q}' status={rr.status_code}")
    try:
        for d in rr.json(): print(f"  domain_id={d.get('domain_id')} | {d.get('domain_name')} | cat={d.get('category_id')} ({d.get('category_name')})")
    except Exception as e: print("  err",e)
