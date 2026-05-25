import os, requests, json
import meli_token
IID="MLM5346655686"; API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_WILBERT"]).json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
s=requests.get(f"{API}/items/{IID}",headers=H,timeout=20).json()
print("item catalog_listing:",s.get("catalog_listing"),"cpid:",s.get("catalog_product_id"))
print("item attrs GTIN/EMPTY:", [(a.get('id'),a.get('value_name')) for a in (s.get('attributes') or []) if a.get('id') in ('GTIN','EMPTY_GTIN_REASON')])
for v in (s.get("variations") or [])[:2]:
    col=[c.get('value_name') for c in (v.get('attribute_combinations') or [])]
    print(f"\nVAR {col} id={v.get('id')}")
    print("  variation attributes:", json.dumps(v.get('attributes') or [], ensure_ascii=False)[:400])
print("DONE")
