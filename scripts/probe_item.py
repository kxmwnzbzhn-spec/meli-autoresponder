import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}
IID="MLM5233454100"
it=requests.get(f"{API}/items/{IID}",headers=H,timeout=15).json()
print("id:",it.get("id"))
print("title:",it.get("title"))
print("status:",it.get("status"),"| sub:",it.get("sub_status"))
print("price:",it.get("price"),it.get("currency_id"),"| available_qty:",it.get("available_quantity"),"| sold:",it.get("sold_quantity"))
print("condition:",it.get("condition"))
print("category_id:",it.get("category_id"))
print("catalog_listing:",it.get("catalog_listing"),"| catalog_product_id:",it.get("catalog_product_id"))
print("domain_id:",it.get("domain_id"))
print("listing_type:",it.get("listing_type_id"))
print("permalink:",it.get("permalink"))
print("pictures:",len(it.get("pictures") or []))
print("health:",it.get("health"))
print("\nATRIBUTOS clave:")
for a in it.get("attributes",[]):
    if a.get("id") in ("BRAND","MODEL","COLOR","POWER_OUTPUT_RMS","WITH_BLUETOOTH","IS_WATERPROOF","GTIN","IP_RATING","SELLER_SKU"):
        print(f"  [{a.get('id')}] {a.get('value_name')}")
