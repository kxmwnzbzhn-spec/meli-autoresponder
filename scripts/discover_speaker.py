"""
Discovery del producto de catálogo de referencia (bocina IP67 35W) para replicar en ASVA.
GET /products/MLMU3924350212 -> atributos, dominio, pictures.
También technical_specs de MLM-SPEAKERS para ver required.
"""
import os, json, requests, meli_token
AT = meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H = {"Authorization": f"Bearer {AT}"}
PID = "MLMU3924350212"

def sec(t): print(f"\n{'='*70}\n{t}\n{'='*70}")

sec(f"GET /products/{PID}")
r = requests.get(f"https://api.mercadolibre.com/products/{PID}", headers=H, timeout=20)
print("status", r.status_code)
if r.status_code == 200:
    p = r.json()
    print("name:", p.get("name"))
    print("domain_id:", p.get("domain_id"))
    print("status:", p.get("status"))
    print("pictures:", len(p.get("pictures") or []))
    print("\nATRIBUTOS:")
    for a in p.get("attributes", []):
        vals = a.get("values") or []
        vn = a.get("value_name")
        print(f"  [{a.get('id')}] {a.get('name')} = {vn}")
else:
    print("body:", r.text[:400])

# technical specs speakers - required
sec("technical_specs MLM-SPEAKERS (required)")
r2 = requests.get("https://api.mercadolibre.com/domains/MLM-SPEAKERS/technical_specs", headers=H, timeout=20)
print("status", r2.status_code)
if r2.status_code == 200:
    def walk(node):
        if isinstance(node, dict):
            if node.get("id") and ("tags" in node or "values" in node or "value_type" in node):
                tags = node.get("tags", {})
                tg = [k for k,v in (tags.items() if isinstance(tags,dict) else []) if v]
                if "required" in tg or "catalog_required" in tg:
                    print(f"  REQUIRED [{node.get('id')}] {node.get('name')}")
            for v in node.values(): walk(v)
        elif isinstance(node, list):
            for v in node: walk(v)
    walk(r2.json())
