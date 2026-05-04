"""Verificar elegibilidad ASVA para crear sugerencias de perfume."""
import os, requests, json
APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]

r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H,timeout=10).json()
uid=me["id"]
print(f"Cuenta: {me['nickname']} ({uid})\n")

# 0) probar varios formatos de domain
for d in ["MLM-PERFUMES","MLM-PERFUMERY","MLM-FRAGRANCES","MLM-PERFUMES_AND_FRAGRANCES"]:
    rr=requests.post("https://api.mercadolibre.com/catalog_suggestions",headers=H,
        json={"site_id":"MLM","domain_id":d,"attributes":[{"id":"BRAND","value_name":"x"}]},timeout=10)
    print(f"  domain {d}: {rr.status_code} {rr.text[:200]}")

# Categoria perfumes nivel hojas
print("\n--- categorias perfumes ---")
def find_perf(cat_id, depth=0):
    r=requests.get(f"https://api.mercadolibre.com/categories/{cat_id}",timeout=10).json()
    name=r.get("name","")
    if "perfu" in name.lower() or "fragancia" in name.lower():
        print(f"  {'  '*depth}{cat_id} {name}")
    for ch in r.get("children_categories",[])[:30]:
        if depth < 3:
            find_perf(ch["id"], depth+1)
find_perf("MLM1246")  # Belleza

# 1) Test POST con perfume placeholder para ver validación
print("\n--- POST /catalog_suggestions test PERFUMES_AND_FRAGRANCES ---")
test_body = {
    "site_id":"MLM",
    "domain_id":"PERFUMES_AND_FRAGRANCES",
    "attributes":[
        {"id":"BRAND","value_name":"Test"},
        {"id":"PERFUME_NAME","value_name":"Test Eau"},
        {"id":"ITEM_VOLUME","value_name":"100 ml"},
        {"id":"PERFUME_TYPE","value_name":"Eau de Parfum"},
        {"id":"GENDER","value_name":"Hombre"},
        {"id":"GTIN","value_name":"1234567890123"},
    ]
}
r=requests.post("https://api.mercadolibre.com/catalog_suggestions",headers=H,json=test_body,timeout=15)
print(f"  status: {r.status_code}")
try:
    body=r.json()
    print(f"  body: {json.dumps(body,indent=2,ensure_ascii=False)[:1500]}")
except:
    print(f"  text: {r.text[:600]}")

# 2) Atributos requeridos del dominio
print("\n--- /domains/PERFUMES_AND_FRAGRANCES/technical_specs ---")
r=requests.get("https://api.mercadolibre.com/domains/PERFUMES_AND_FRAGRANCES/technical_specs?site_id=MLM",headers=H,timeout=10)
print(f"  {r.status_code}: {r.text[:800]}")

# 3) Categoría perfumes
print("\n--- search MLM categories perfumes ---")
r=requests.get("https://api.mercadolibre.com/sites/MLM/categories",headers=H,timeout=10).json()
for c in r:
    if "perfu" in c.get("name","").lower() or "fragancia" in c.get("name","").lower() or "belleza" in c.get("name","").lower():
        print(f"  {c['id']} {c['name']}")
