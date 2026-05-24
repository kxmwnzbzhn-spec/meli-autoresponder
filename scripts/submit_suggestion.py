import os, requests, json
import meli_token

CPID = "MLM52113823"; DOM = "MLM-PERFUMES"
API = "https://api.mercadolibre.com"
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]
T = meli_token.refresh(RT).json()["access_token"]
H  = {"Authorization": f"Bearer {T}"}
HJ = {"Authorization": f"Bearer {T}", "Content-Type": "application/json"}
PICS = ["897724-MLM112154514469_052026","840560-MLM112155272235_052026",
        "751916-MLM111152110628_052026","606658-MLM112155475559_052026"]

p = requests.get(f"{API}/products/{CPID}", headers=H, timeout=20).json()

CHANGES = {"BRAND": "The Alchemia Lab", "MPN": "TAL-FDN-100ML"}
attrs = []
for a in (p.get("attributes") or []):
    aid = a.get("id")
    if aid in CHANGES:                               # valor nuevo (sin id, MELI lo crea)
        attrs.append({"id": aid, "value_name": CHANGES[aid]})
        continue
    vals = a.get("values") or []
    if vals and all(v.get("id") for v in vals):      # mirror por value_id (multi o single)
        attrs.append({"id": aid, "values": [{"id": v["id"]} for v in vals]})
    elif a.get("value_id"):
        attrs.append({"id": aid, "value_id": a["value_id"]})
    elif a.get("value_name"):
        attrs.append({"id": aid, "value_name": a["value_name"]})

print(f"attrs a enviar: {len(attrs)}  (BRAND/MPN como valor nuevo)")
body = {"domain_id": DOM, "catalog_product_id": CPID, "type": "edit",
        "attributes": attrs, "pictures": [{"id": p_} for p_ in PICS]}
r = requests.post(f"{API}/catalog_suggestions", headers=HJ, json=body, timeout=40)
print("http=", r.status_code)
try:
    j = r.json()
    cs = j.get("cause") if isinstance(j, dict) else None
    if cs:
        for c in cs: print("  cause:", c.get("code"), c.get("message","")[:90])
    else:
        print(json.dumps(j, ensure_ascii=False)[:600])
except Exception:
    print(r.text[:600])
print("DONE")
