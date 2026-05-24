import os, requests
import meli_token

IID = "MLM2950839631"
PRICE = 1999
EXPECTED_SELLER = 3364413125  # Yiriam / YC_NEW

RT = os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
AT = meli_token.refresh(RT).json()["access_token"]
H  = {"Authorization": f"Bearer {AT}"}
HJ = {**H, "Content-Type": "application/json"}

it = requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=id,seller_id,status,available_quantity,price,catalog_product_id,catalog_listing,title", headers=H, timeout=20).json()
print(f"ITEM {IID}: seller={it.get('seller_id')} status={it.get('status')} qty={it.get('available_quantity')} price={it.get('price')} cpid={it.get('catalog_product_id')} catalog_listing={it.get('catalog_listing')} title={it.get('title','')[:55]!r}")

if it.get("seller_id") != EXPECTED_SELLER:
    print(f"ABORT: no es Yiriam (seller={it.get('seller_id')})"); raise SystemExit(1)

body = {"status": "active", "price": PRICE}
if (it.get("available_quantity") or 0) < 1:
    body["available_quantity"] = 1
r = requests.put(f"https://api.mercadolibre.com/items/{IID}", headers=HJ, json=body, timeout=20)
print(f"PUT {body} -> {r.status_code} {('' if r.status_code==200 else r.text[:200])}")

fin = requests.get(f"https://api.mercadolibre.com/items/{IID}?attributes=status,available_quantity,price,catalog_product_id", headers=H, timeout=20).json()
print(f"FINAL status={fin.get('status')} qty={fin.get('available_quantity')} price={fin.get('price')} cpid={fin.get('catalog_product_id')}")
print("DONE")
