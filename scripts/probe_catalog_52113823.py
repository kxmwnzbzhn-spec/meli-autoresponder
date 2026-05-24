import os, requests, json
import meli_token

CPID = "MLM52113823"
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
H = {"Authorization": f"Bearer {T}"}

p = requests.get(f"{API}/products/{CPID}", headers=H, timeout=20).json()
print("NAME:", p.get("name"))
print("STATUS:", p.get("status"), "| DOMAIN:", p.get("domain_id"), "| CATEGORY:", p.get("category_id"))
print("FAMILY:", p.get("family_name"), "| pictures:", len(p.get("pictures") or []))
print("BUYBOX_WINNER:", (p.get("buy_box_winner") or {}).get("item_id"), (p.get("buy_box_winner") or {}).get("price"))
print("\n--- MAIN ATTRIBUTES ---")
for a in (p.get("main_features") or []):
    print("  feat:", a.get("text"))
for a in (p.get("attributes") or []):
    vn = a.get("value_name")
    print(f"  [{a.get('id')}] {a.get('name')} = {vn}")
print("\n--- short_description present:", bool(p.get("short_description")))
# catalog quality / suggestions capability probe
print("\n--- quality probe ---")
for path in [f"/products/{CPID}/quality", f"/catalog_quality/products/{CPID}"]:
    try:
        r = requests.get(f"{API}{path}", headers=H, timeout=15)
        print(f"  GET {path} -> {r.status_code} {r.text[:140]}")
    except Exception as e:
        print(f"  GET {path} EXC {e}")
print("DONE")
