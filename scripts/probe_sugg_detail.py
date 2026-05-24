import os, requests, json
import meli_token
API="https://api.mercadolibre.com"
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
T=meli_token.refresh(RT).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

SID="MLM5396839552"
d=requests.get(f"{API}/catalog_suggestions/{SID}",headers=H,timeout=20).json()
print("=== suggestion detail ===")
print(json.dumps(d, ensure_ascii=False)[:1500])
print("\ntype:", d.get("type"), "| status:", d.get("status"), "| catalog_product_id:", d.get("catalog_product_id"), "| product_id:", d.get("product_id"))

# probar variantes de EDICION para apuntar al producto existente (sin enviar, solo ver error/tipo)
print("\n=== probe edit-type bodies (incompletos, esperar 400) ===")
for body in [
    {"domain_id":"MLM-PERFUMES","type":"EDIT","catalog_product_id":"MLM52113823"},
    {"domain_id":"MLM-PERFUMES","type":"edit","product_id":"MLM52113823"},
    {"domain_id":"MLM-PERFUMES","type":"DOMAIN_CHANGE","catalog_product_id":"MLM52113823"},
]:
    r=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=body,timeout=30)
    print(f"  {json.dumps(body)} -> {r.status_code} {r.text[:160]}")
print("DONE")
