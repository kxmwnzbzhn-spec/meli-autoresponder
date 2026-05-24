"""
DISCOVERY para piloto Audífonos ASVA Buds 2.
1) Token ASVA via Worker (meli_token)
2) domain_discovery para 'audifonos inalambricos bluetooth'
3) technical_specs del dominio de audífonos (MLM-HEADPHONES)
   -> imprime atributos: id, name, tags (required/catalog_required), value lists
Output: discover_buds2.json
"""
import os, json, requests, meli_token

AT = meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H = {"Authorization": f"Bearer {AT}"}
out = {}

def sec(t): print(f"\n{'='*70}\n{t}\n{'='*70}")

# users/me
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=15).json()
print("ASVA uid:", me.get("id"), "nick:", me.get("nickname"))
out["uid"] = me.get("id")

# 1) domain discovery
sec("domain_discovery")
for q in ["audifonos inalambricos bluetooth", "audifonos bluetooth tws", "audifonos in ear"]:
    r = requests.get("https://api.mercadolibre.com/sites/MLM/domain_discovery/search",
                     params={"q": q, "limit": 5}, headers=H, timeout=15)
    print(f"\nq='{q}' status={r.status_code}")
    try:
        rows = r.json()
        for d in rows:
            print(f"  domain_id={d.get('domain_id')} | domain={d.get('domain_name')} | cat={d.get('category_id')} ({d.get('category_name')})")
        out.setdefault("domain_discovery", {})[q] = rows
    except Exception as e:
        print("  err", e, r.text[:200])

# 2) technical specs del dominio headphones
DOMAIN = "MLM-HEADPHONES"
sec(f"technical_specs {DOMAIN}")
r = requests.get(f"https://api.mercadolibre.com/domains/{DOMAIN}/technical_specs",
                 headers=H, timeout=20)
print("status", r.status_code)
ts = None
if r.status_code == 200:
    ts = r.json()
    out["technical_specs"] = ts
    # technical_specs trae groups -> components -> attributes
    def walk(node, depth=0):
        if isinstance(node, dict):
            if node.get("id") and ("tags" in node or "value_type" in node or "values" in node):
                aid = node.get("id"); name = node.get("name")
                tags = node.get("tags", {})
                tg = [k for k,v in (tags.items() if isinstance(tags,dict) else []) if v]
                vals = node.get("values") or []
                vsample = ", ".join(v.get("name","?") for v in vals[:8]) if vals else ""
                flag = ""
                if "required" in tg or "catalog_required" in tg: flag = " *** REQUIRED ***"
                print(f"  [{aid}] {name} tags={tg}{flag}")
                if vsample: print(f"       valores: {vsample}{' …' if len(vals)>8 else ''}")
            for v in node.values():
                walk(v, depth+1)
        elif isinstance(node, list):
            for v in node: walk(v, depth+1)
    walk(ts)
else:
    print("body:", r.text[:400])
    # fallback: probar attributes endpoint
    r2 = requests.get(f"https://api.mercadolibre.com/domains/{DOMAIN}/attributes", headers=H, timeout=20)
    print("attributes status", r2.status_code, r2.text[:300])
    if r2.status_code == 200:
        out["attributes_fallback"] = r2.json()

import pathlib
pathlib.Path("discover_buds2.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
print("\n[OK] discover_buds2.json escrito")
