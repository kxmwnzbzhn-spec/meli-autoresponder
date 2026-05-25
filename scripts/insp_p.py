import os, requests, json
import meli_token
CP="MLM65349937"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
p=requests.get(f"{API}/products/{CP}",headers=H,timeout=20).json()
print("NAME:",p.get("name"))
print("domain:",p.get("domain_id"),"| category:",p.get("category_id"),"| status:",p.get("status"))
print("pictures:",len(p.get("pictures") or []))
print("ATTRIBUTES:")
for a in (p.get("attributes") or []):
    print("  ",a.get("id"),"=",a.get("value_name"))
# category attrs: required + SIZE/variation
cat=p.get("category_id")
if cat:
    ca=requests.get(f"{API}/categories/{cat}/attributes",headers=H,timeout=20).json()
    print("\nCATEGORY required/variation attrs:")
    for a in ca:
        tags=a.get("tags") or {}
        if tags.get("required") or tags.get("catalog_required") or tags.get("allow_variations") or a.get("id") in ("SIZE","SIZE_GRID_ID","GENDER","BRAND","EMPTY_GTIN_REASON","GTIN"):
            vals=[v.get("name") for v in (a.get("values") or [])][:6]
            print(f"  {a.get('id')} [{','.join(k for k,v in tags.items() if v)}] vals={vals}")
print("DONE")
