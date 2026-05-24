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

# base: todos los atributos existentes (excepto BRAND/MPN) por value_id
base = []
for a in (p.get("attributes") or []):
    aid = a.get("id")
    if aid in ("BRAND", "MPN"): continue
    vals = a.get("values") or []
    if vals and all(v.get("id") for v in vals):
        base.append({"id": aid, "values": [{"id": v["id"]} for v in vals]})
    elif a.get("value_id"):
        base.append({"id": aid, "value_id": a["value_id"]})

def brand_mpn(fmt):
    if fmt == "name":
        return [{"id":"BRAND","values":[{"name":"The Alchemia Lab"}]},
                {"id":"MPN","values":[{"name":"TAL-FDN-100ML"}]}]
    if fmt == "value_name":
        return [{"id":"BRAND","values":[{"value_name":"The Alchemia Lab"}]},
                {"id":"MPN","values":[{"value_name":"TAL-FDN-100ML"}]}]

TITLE = "Perfume The Alchemia Lab Flor de Nopal Mexico en la Piel Eau de Parfum 100 ml Unisex"
trials = [
    ("title_field",     {"title": TITLE}),
    ("name_field",      {"name": TITLE}),
    ("no_title",        {}),
]
for label, extra in trials:
    body = {"domain_id": DOM, "catalog_product_id": CPID, "type": "edit",
            "attributes": base + brand_mpn("name"), "pictures": [{"id": x} for x in PICS]}
    body.update(extra)
    r = requests.post(f"{API}/catalog_suggestions", headers=HJ, json=body, timeout=40)
    j = r.json() if r.headers.get("content-type","").startswith("application/json") else r.text
    cs = j.get("cause") if isinstance(j, dict) else None
    summ = " | ".join(f"{c.get('code')}:{c.get('message','')[:55]}" for c in cs) if cs else (json.dumps(j, ensure_ascii=False)[:250] if isinstance(j,dict) else str(j)[:250])
    print(f"[{label:12}] http={r.status_code}  {summ}")
    if r.status_code < 300:
        print("  >>> SUCCESS:", json.dumps(j, ensure_ascii=False)[:500]); break
print("DONE")
