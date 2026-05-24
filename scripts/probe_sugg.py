import os, requests, json
import meli_token

CPID = "MLM52113823"; DOM = "MLM-PERFUMES"
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
H = {"Authorization": f"Bearer {T}"}

me = requests.get(f"{API}/users/me", headers=H, timeout=15).json()
print("ME:", me.get("id"), me.get("nickname"))

cands = [
    f"/catalog_quality/{CPID}",
    f"/catalog_quality?product_id={CPID}",
    f"/catalog_suggestions/{CPID}",
    f"/catalog_suggestions/search?product_id={CPID}",
    f"/catalog_suggestions?product_id={CPID}",
    f"/products/{CPID}/suggestions",
    f"/catalog/suggestions?product_id={CPID}",
    f"/catalog/products/{CPID}/suggestions",
    f"/users/{me.get('id')}/catalog_suggestions/search",
    f"/products/{CPID}/quality_score",
]
print("\n--- GET probes ---")
for path in cands:
    try:
        r = requests.get(f"{API}{path}", headers=H, timeout=15)
        print(f"  {r.status_code}  {path}  ::  {r.text[:120]}")
    except Exception as e:
        print(f"  EXC {path} :: {e}")

print("\n--- domain technical specs (atributos editables) ---")
for path in [f"/domains/{DOM}/technical_specs", f"/catalog_domains/{DOM}/attributes"]:
    try:
        r = requests.get(f"{API}{path}", headers=H, timeout=20)
        print(f"  {r.status_code}  {path}  len={len(r.text)}")
    except Exception as e:
        print(f"  EXC {path} :: {e}")
print("DONE")
