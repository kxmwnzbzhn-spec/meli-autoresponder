import os, requests, json
import meli_token

CPID = "MLM52113823"; DOM = "MLM-PERFUMES"
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
HJ = {"Authorization": f"Bearer {T}", "Content-Type": "application/json"}

# SOLO cuerpos INCOMPLETOS -> esperamos 400 validation_error que liste campos requeridos.
# NO enviamos un cuerpo completo para no crear una sugerencia real.
bodies = [
    {},
    {"type": "edit"},
    {"catalog_product_id": CPID},
    {"catalog_product_id": CPID, "type": "edit"},
    {"domain_id": DOM, "catalog_product_id": CPID, "type": "edit"},
]
for b in bodies:
    try:
        r = requests.post(f"{API}/catalog_suggestions", headers=HJ, json=b, timeout=20)
        print(f"\nBODY={json.dumps(b)}")
        print(f"  -> {r.status_code}")
        print(f"  {r.text[:500]}")
    except Exception as e:
        print(f"\nBODY={json.dumps(b)} EXC {e}")
print("\nDONE")
