"""
v4: aislar la causa del 2006. Hipótesis a testear:
  H1: BRAND="Asvaelectronics" no está en el brand registry → usar BRAND="Genérica" con value_id
  H2: falta category_id en el body → agregar
  H3: pictures rotas → enviar sin pictures
  H4: app no tiene scope catalog_suggestions → check via /applications/{app_id}
  H5: endpoint deprecated → probar variantes
"""
import os, json, hashlib, requests, pathlib

APP_ID = "5211907102822632"
APP_SECRET = os.environ["MELI_APP_SECRET"]
RT = os.environ["MELI_REFRESH_TOKEN_ASVA"]

def section(t):
    print(f"\n{'='*72}\n=== {t}\n{'='*72}")

# OAuth
r = requests.post("https://api.mercadolibre.com/oauth/token",
                  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},
                  timeout=15).json()
AT = r["access_token"]
H = {"Authorization": f"Bearer {AT}"}
HJ = {**H, "Content-Type": "application/json"}
me = requests.get("https://api.mercadolibre.com/users/me", headers=H, timeout=10).json()
UID = me["id"]
print(f"asva uid={UID}")

results = {}

# H4: scopes de la app
section("H4: scopes app")
rr = requests.get(f"https://api.mercadolibre.com/applications/{APP_ID}", headers=H, timeout=10)
print(f"  GET /applications/{APP_ID} -> {rr.status_code}")
if rr.status_code == 200:
    j = rr.json()
    print(f"  scopes: {j.get('scopes') or j.get('scope')}")
    print(f"  active_topics: {j.get('active_topics')}")
    print(f"  callback: {j.get('callback')}")
    results["app_scopes"] = j.get("scopes") or j.get("scope")
else:
    print(f"  body: {rr.text[:300]}")

# Permission de catalog_suggestion del usuario
section("user permissions / catalog state")
rr = requests.get(f"https://api.mercadolibre.com/users/{UID}", headers=H, timeout=10).json()
print(f"  status: {rr.get('status')}")
print(f"  permalink: {rr.get('permalink')}")
print(f"  user_type: {rr.get('user_type')}")
print(f"  seller_reputation: power_seller_status={rr.get('seller_reputation',{}).get('power_seller_status')}")
print(f"  shopping_categories: {rr.get('shopping_categories')}")

# Brand registry - listar brands cuyo value_name match
section("brand registry sniff: BRAND attribute en MLM59800")
rr = requests.get("https://api.mercadolibre.com/categories/MLM59800/attributes", headers=H, timeout=10).json()
brand_attr = next((a for a in rr if a.get("id")=="BRAND"), None)
if brand_attr:
    vals = brand_attr.get("values") or []
    print(f"  total BRAND values registrados: {len(vals)}")
    # Buscar Asva, ASVA, generica, jbl, ...
    for kw in ["asva","gener","jbl","sonix","x35"]:
        match = [v for v in vals if kw in (v.get("name") or "").lower()][:3]
        if match:
            for m in match:
                print(f"    match '{kw}': id={m.get('id')} name={m.get('name')}")

# EAN
seed = "asvaelectronics::flipi7"
nine = "".join(c for c in hashlib.md5(seed.encode()).hexdigest() if c.isdigit())[:9].ljust(9,"0")
body12 = "290"+nine
EAN = body12 + str((10 - sum(int(d)*(3 if i%2 else 1) for i,d in enumerate(body12))%10)%10)
print(f"\n  ean13={EAN}")

def post_attempt(label, body):
    print(f"\n  -- {label}")
    print(f"     body={json.dumps(body,ensure_ascii=False)[:400]}")
    rr = requests.post("https://api.mercadolibre.com/catalog_suggestions", headers=HJ, json=body, timeout=15)
    print(f"     status={rr.status_code}")
    try:
        rb = rr.json()
        print(f"     body[:400]={json.dumps(rb,ensure_ascii=False)[:400]}")
        return {"status": rr.status_code, "body": rb}
    except Exception:
        print(f"     raw[:200]={rr.text[:200]}")
        return {"status": rr.status_code, "raw": rr.text[:300]}

# H1: usar BRAND con value_id Genérica
section("H1: BRAND=Genérica con value_id")
results["h1"] = post_attempt("h1", {
    "site_id":"MLM","domain_id":"MLM-SPEAKERS",
    "attributes":[
        {"id":"BRAND","value_id":"276243","value_name":"Genérica"},
        {"id":"MODEL","value_name":"Flipi7"},
        {"id":"COLOR","value_id":"52049","value_name":"Negro"},
        {"id":"GTIN","value_name":EAN},
    ],
})

# H2: agregar category_id
section("H2: + category_id")
results["h2"] = post_attempt("h2", {
    "site_id":"MLM","domain_id":"MLM-SPEAKERS","category_id":"MLM59800",
    "attributes":[
        {"id":"BRAND","value_id":"276243","value_name":"Genérica"},
        {"id":"MODEL","value_name":"Flipi7"},
        {"id":"COLOR","value_id":"52049","value_name":"Negro"},
        {"id":"GTIN","value_name":EAN},
    ],
})

# H3: SOLO BRAND registrada (mínimo absoluto)
section("H3: ultra-mínimo - solo BRAND registrada")
results["h3"] = post_attempt("h3", {
    "site_id":"MLM","domain_id":"MLM-SPEAKERS",
    "attributes":[
        {"id":"BRAND","value_id":"276243","value_name":"Genérica"},
    ],
})

# H5: probar endpoints alternativos
section("H5: endpoints alternativos")
alts = [
    ("catalog_suggestions/items", {"site_id":"MLM","domain_id":"MLM-SPEAKERS","attributes":[{"id":"BRAND","value_id":"276243","value_name":"Genérica"}]}),
    ("catalog/suggestions", {"site_id":"MLM","domain_id":"MLM-SPEAKERS","attributes":[{"id":"BRAND","value_id":"276243","value_name":"Genérica"}]}),
    (f"users/{UID}/catalog_suggestions", {"site_id":"MLM","domain_id":"MLM-SPEAKERS","attributes":[{"id":"BRAND","value_id":"276243","value_name":"Genérica"}]}),
]
for path, body in alts:
    rr = requests.post(f"https://api.mercadolibre.com/{path}", headers=HJ, json=body, timeout=10)
    print(f"  POST /{path} -> {rr.status_code}: {rr.text[:200]}")
    results[f"alt_{path.replace('/','_')}"] = {"status": rr.status_code, "raw": rr.text[:200]}

# H4 extra: get user_id_apps con catalog scopes
section("H4 extra: my apps for this seller")
rr = requests.get(f"https://api.mercadolibre.com/users/{UID}/applications", headers=H, timeout=10)
print(f"  status={rr.status_code}")
print(f"  body[:1500]={rr.text[:1500]}")
results["user_apps"] = {"status": rr.status_code, "body": rr.text[:2000]}

pathlib.Path("probe_v4_result.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
print("\n[OK] wrote probe_v4_result.json")
