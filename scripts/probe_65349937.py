import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}
def sec(t): print(f"\n=== {t} ===")
sec("GET /products/MLM65349937")
r=requests.get(f"{API}/products/MLM65349937",headers=H,timeout=20)
print("status",r.status_code)
if r.status_code==200:
    d=r.json()
    print("name:",d.get("name"))
    print("domain_id:",d.get("domain_id"),"| status:",d.get("status"))
    print("attributes:")
    for a in d.get("attributes",[]):
        print(f"   [{a.get('id')}] {a.get('name')} = {a.get('value_name')}")
else:
    print("body:",r.text[:150])
    # buscar en items ASVA por si lo tienen, e items del catálogo
    sec("buscar match en ASVA items")
    UID=requests.get(f"{API}/users/me",headers=H,timeout=15).json()["id"]
    # no sé el nombre; intento GET items del producto
    sec("GET /products/MLM65349937/items")
    r2=requests.get(f"{API}/products/MLM65349937/items",headers=H,timeout=15)
    print("status",r2.status_code, r2.text[:200])
