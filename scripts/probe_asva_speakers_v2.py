"""
Probe v2: descubrir el domain_id real para bocinas BT, encontrar el cpid real
del producto referenciado, y reintentar POST con body más completo.
"""
import os, json, requests, sys, pathlib

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]

result = {}

def section(t):
    print(f"\n{'='*72}\n=== {t}\n{'='*72}")

# Token
r = requests.post(
    "https://api.mercadolibre.com/oauth/token",
    data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
    timeout=15,
).json()
AT = r["access_token"]
H = {"Authorization": f"Bearer {AT}"}
HJ = {**H, "Content-Type": "application/json"}

me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
UID = me["id"]
print(f"asva uid={UID} nick={me['nickname']}")
result["uid"] = UID

# 1) domain_discovery para bocina bluetooth
section("1) /sites/MLM/domain_discovery/search?q=bocina bluetooth portatil")
for q in ["bocina bluetooth portatil", "bocina portatil ip67", "altavoz bluetooth", "speaker bluetooth"]:
    rr = requests.get(f"https://api.mercadolibre.com/sites/MLM/domain_discovery/search",
                      params={"limit":5, "q": q}, headers=H, timeout=10)
    print(f"\n  q='{q}' -> {rr.status_code}")
    try:
        body = rr.json()
        for d in (body if isinstance(body, list) else [])[:5]:
            print(f"    domain_id={d.get('domain_id')}  cat={d.get('category_id')}  name={d.get('domain_name')}")
        if isinstance(body, list) and body:
            result.setdefault("domain_discovery", {})[q] = body[:3]
    except Exception:
        print(f"    raw: {rr.text[:300]}")

# 2) Buscar el catalog product por keyword
section("2) /products/search por keywords del URL")
queries = [
    "bocina bluetooth portatil ip67 35w negro",
    "bocina bluetooth ip67 bass 35w",
    "speaker bluetooth ip67 35w",
]
found_cpids = []
for q in queries:
    rr = requests.get("https://api.mercadolibre.com/products/search",
                      params={"site_id":"MLM","status":"active","q":q,"limit":5},
                      headers=H, timeout=15)
    print(f"\n  q='{q}' -> {rr.status_code}")
    try:
        body = rr.json()
        if "results" in body:
            for p in body["results"][:5]:
                pid = p.get("id")
                name = p.get("name","")[:80]
                dom = p.get("domain_id")
                cat = p.get("category_id")
                print(f"    {pid}  dom={dom}  cat={cat}  name={name}")
                found_cpids.append({"id": pid, "domain_id": dom, "category_id": cat, "name": name})
        else:
            print(f"    body: {json.dumps(body)[:300]}")
    except Exception as e:
        print(f"    err: {e} raw: {rr.text[:300]}")
result["found_cpids"] = found_cpids[:10]

# 3) Si encontramos algún CPID con MLMU, traer detalle completo
section("3) Detalle del primer CPID que matchee 'bocina ... 35w'")
ref = None
for fc in found_cpids:
    n = (fc.get("name") or "").lower()
    if "35" in n and "bluetooth" in n:
        ref = fc
        break
if not ref and found_cpids:
    ref = found_cpids[0]

if ref:
    cpid = ref["id"]
    print(f"  Inspecting cpid={cpid}")
    rr = requests.get(f"https://api.mercadolibre.com/products/{cpid}", headers=H, timeout=15)
    print(f"  /products/{cpid} -> {rr.status_code}")
    if rr.status_code == 200:
        p = rr.json()
        result["ref_product"] = {
            "id": p.get("id"),
            "name": p.get("name"),
            "domain_id": p.get("domain_id"),
            "category_id": p.get("category_id"),
            "status": p.get("status"),
            "pictures_count": len(p.get("pictures") or []),
            "pictures_first5": [pic.get("url") for pic in (p.get("pictures") or [])[:5]],
            "main_features": [mf.get("text","")[:150] for mf in (p.get("main_features") or [])][:6],
            "attributes": [
                {"id": a.get("id"), "name": a.get("name"), "value_name": a.get("value_name")}
                for a in (p.get("attributes") or [])
            ],
        }
        # imprimir compacto
        print(f"  name: {p.get('name')}")
        print(f"  domain_id: {p.get('domain_id')}")
        print(f"  category_id: {p.get('category_id')}")
        print(f"  pictures: {len(p.get('pictures') or [])}")
        print("  attrs:")
        for a in (p.get("attributes") or [])[:30]:
            print(f"    {a.get('id'):28} = {a.get('value_name')}")

# 4) Si conseguimos un domain_id real, probar technical_specs y reintentar POST
real_dom = None
if "ref_product" in result:
    real_dom = result["ref_product"].get("domain_id")
elif found_cpids:
    real_dom = found_cpids[0].get("domain_id")

if real_dom:
    section(f"4) GET /domains/{real_dom}/technical_specs")
    rr = requests.get(f"https://api.mercadolibre.com/domains/{real_dom}/technical_specs?site_id=MLM",
                      headers=H, timeout=15)
    print(f"  status={rr.status_code}")
    try:
        spec = rr.json()
        # extraer required attributes
        req_attrs = []
        for grp in (spec.get("groups") or []):
            for c in (grp.get("components") or []):
                tags = c.get("tags") or []
                if "required" in tags or c.get("required"):
                    req_attrs.append({
                        "id": c.get("id"),
                        "label": c.get("label") or c.get("text"),
                        "tags": tags,
                    })
        print(f"  required_attrs: {json.dumps(req_attrs, indent=2, ensure_ascii=False)[:2000]}")
        result["domain_required_attrs"] = req_attrs
    except Exception as e:
        print(f"  parse err: {e}; raw: {rr.text[:600]}")

    # POST sondeo con body más completo
    section(f"5) POST /catalog_suggestions sondeo body completo en {real_dom}")
    body = {
        "site_id": "MLM",
        "domain_id": real_dom,
        "attributes": [
            {"id":"BRAND","value_name":"ProbeBrand"},
            {"id":"MODEL","value_name":"PB-35W-BK"},
            {"id":"COLOR","value_name":"Negro"},
            {"id":"POWER","value_name":"35 W"},
            {"id":"ITEM_CONDITION","value_name":"Nuevo"},
            {"id":"GTIN","value_name":"7501234567890"},
            {"id":"IS_BLUETOOTH","value_name":"Sí"},
            {"id":"IS_WATERPROOF","value_name":"Sí"},
            {"id":"WATERPROOF_RATING","value_name":"IP67"},
        ],
        "pictures": [
            {"url":"https://http2.mlstatic.com/D_NQ_NP_2X_846498-MLU79832245996_102024-F.webp"},
            {"url":"https://http2.mlstatic.com/D_NQ_NP_2X_651620-MLU79832245995_102024-F.webp"},
            {"url":"https://http2.mlstatic.com/D_NQ_NP_2X_999999-MLU99999999999_102024-F.webp"},
        ],
    }
    rr = requests.post("https://api.mercadolibre.com/catalog_suggestions",
                       headers=HJ, json=body, timeout=20)
    print(f"  status={rr.status_code}")
    try:
        rb = rr.json()
        print(json.dumps(rb, indent=2, ensure_ascii=False)[:3000])
        result["probe_post_full"] = {"status": rr.status_code, "body": rb}
    except Exception:
        print(f"  raw: {rr.text[:1000]}")
        result["probe_post_full"] = {"status": rr.status_code, "text": rr.text[:1500]}

# 5) También probar POST con body MÍNIMO contra real_dom (descartar 500=payload vs 500=server)
if real_dom:
    section(f"6) POST minimal en {real_dom}")
    rr = requests.post("https://api.mercadolibre.com/catalog_suggestions",
                       headers=HJ,
                       json={"site_id":"MLM","domain_id":real_dom,
                             "attributes":[{"id":"BRAND","value_name":"X"}]}, timeout=15)
    print(f"  status={rr.status_code}")
    try:
        rb = rr.json()
        print(json.dumps(rb, indent=2, ensure_ascii=False)[:1500])
        result["probe_post_minimal"] = {"status": rr.status_code, "body": rb}
    except:
        result["probe_post_minimal"] = {"status": rr.status_code, "text": rr.text[:800]}

# Dump
out = pathlib.Path("probe_asva_speakers_v2_result.json")
out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
print(f"\n[OK] wrote {out}")
