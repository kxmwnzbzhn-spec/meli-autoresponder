import os, requests, json
import meli_token
IID="MLM5346655686"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_WILBERT"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
s=requests.get(f"{API}/items/{IID}",headers=H,timeout=20).json()
print("TITLE:",s.get("title"))
print("status:",s.get("status"),"| seller:",s.get("seller_id"),"| cat:",s.get("category_id"),"| cpid:",s.get("catalog_product_id"),"| catalog_listing:",s.get("catalog_listing"))
print("price:",s.get("price"),"| listing_type:",s.get("listing_type_id"),"| condition:",s.get("condition"),"| qty:",s.get("available_quantity"))
print("pictures:",len(s.get("pictures") or []))
print("\nATTRIBUTES (no-variation):")
for a in (s.get("attributes") or []):
    if a.get("id") in ("BRAND","MODEL","LINE","GTIN","EMPTY_GTIN_REASON","ITEM_CONDITION","MODEL_CODE"):
        print("  ",a.get("id"),"=",a.get("value_name"))
vs=s.get("variations") or []
print(f"\nVARIATIONS: {len(vs)}")
for v in vs:
    cmb={c.get("name"):c.get("value_name") for c in (v.get("attribute_combinations") or [])}
    print(f"  id={v.get('id')} {cmb} qty={v.get('available_quantity')} price={v.get('price')} pics={len(v.get('picture_ids') or [])}")
d=requests.get(f"{API}/items/{IID}/description",headers=H,timeout=15).json()
print("\nDESCRIPTION (actual):", json.dumps((d.get('plain_text') or '')[:300], ensure_ascii=False))
print("DONE")
