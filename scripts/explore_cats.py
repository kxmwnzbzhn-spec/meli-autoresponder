"""Explore MELI MX category alternatives to MLM1271 for publishing perfumes."""
import os, requests, json
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]},timeout=20).json()
AT=r["access_token"]
H={"Authorization":f"Bearer {AT}"}

# 1) Current category baseline
print("=== MLM1271 (Fragancias) baseline ===")
c=requests.get(f"{API}/categories/MLM1271",headers=H,timeout=10).json()
print(f"  name={c.get('name')} path={[p.get('name') for p in (c.get('path_from_root') or [])]}")
print(f"  settings: condition={c.get('settings',{}).get('item_conditions')} max_title={c.get('settings',{}).get('max_title_length')}")
ca=requests.get(f"{API}/categories/MLM1271/attributes",headers=H,timeout=10).json()
print(f"  Required attrs:")
for a in ca:
    if (a.get("tags") or {}).get("required"):
        print(f"    - {a.get('id')} ({a.get('name')}) type={a.get('value_type')}")

# 2) Discover alternative categories via search
print("\n=== Domain discovery — perfume-adjacent queries ===")
candidates=set()
queries=[
    "perfume","fragancia","colonia","loción","eau de parfum","eau de toilette",
    "aromaterapia","aceite esencial","esencia","aromatizante","extracto aromático",
    "kit perfumes","muestrario perfumes","decant perfume","fragancias originales",
    "splash","body mist","cuerpo aroma"
]
for q in queries:
    dd=requests.get(f"{API}/sites/MLM/domain_discovery/search",
        params={"q":q,"limit":5},headers=H,timeout=10).json()
    if isinstance(dd,list):
        for d in dd[:5]:
            cat=d.get("category_id"); name=d.get("category_name")
            domain=d.get("domain_name")
            if cat and cat!="MLM1271":
                candidates.add((cat,name,domain))

# 3) Also probe specific known categories
KNOWN=[
    ("MLM5717","Cosméticos y Maquillaje"),
    ("MLM1246","Belleza y Cuidado Personal"),
    ("MLM431079","Lotes de Belleza (suposicion)"),
    ("MLM431078","Lotes de Ropa"),
    ("MLM3187","Aceites Esenciales (suposicion)"),
    ("MLM411","Aromaterapia"),
    ("MLM3137","Salud"),
    ("MLM435440","Cuidado Personal Otros"),
    ("MLM2347","Cremas y Tratamientos"),
]
for cid,_ in KNOWN: candidates.add((cid,None,None))

print(f"\nCandidates discovered: {len(candidates)}")

# 4) Per candidate: enumerate name, path, requireds, item_conditions
print("\n=== Detail per candidate category ===")
report=[]
for cat,_,domain in candidates:
    try:
        ci=requests.get(f"{API}/categories/{cat}",headers=H,timeout=10).json()
    except: continue
    if ci.get("error"): continue
    name=ci.get("name")
    path=" > ".join(p.get("name","") for p in (ci.get("path_from_root") or []))
    settings=ci.get("settings",{}) or {}
    try:
        a=requests.get(f"{API}/categories/{cat}/attributes",headers=H,timeout=10).json()
    except: a=[]
    reqs=[(x.get("id"),x.get("name")) for x in a if (x.get("tags") or {}).get("required")]
    has_gtin_req="GTIN" in [r[0] for r in reqs]
    has_brand_req="BRAND" in [r[0] for r in reqs]
    children=ci.get("children_categories") or []
    report.append({
        "cat":cat,
        "name":name,
        "path":path,
        "domain":(ci.get("settings",{}).get("catalog_domain") or domain),
        "n_required":len(reqs),
        "has_gtin":has_gtin_req,
        "has_brand":has_brand_req,
        "req_names":[r[1] for r in reqs[:8]],
        "n_children":len(children),
        "buying_allowed":settings.get("buying_allowed"),
        "conditions":settings.get("item_conditions"),
    })

report.sort(key=lambda x:(x["has_gtin"], x["n_required"]))
print(json.dumps(report,ensure_ascii=False,indent=2))
