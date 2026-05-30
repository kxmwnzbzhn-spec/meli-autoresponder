"""Adrián batch 1: 5 perfumes. Buscar top-vendido por nombre, evitar 200ml + dups.
Estrategia per perfume:
  1) GET /products/search?q=...&site_id=MLM → lista de CPIDs candidatos
  2) Para cada candidato, GET /products/{cpid} → leer NAME y attributes para filtrar tamaño
  3) Filtrar: name no contiene "200 ml", name CONTIENE el tamaño objetivo si se especifica
  4) Pick el primero válido
  5) POST /items con catalog_listing=True (sin title — heredado)
"""
import os, requests, time, re
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_AH"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_AH={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]
print(f"seller={UID} nick={me.get('nickname')}")

# Existing CPIDs en Adrián para no duplicar
existing_cpids=set()
for st in ("active","paused","under_review"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        for i in range(0,len(res),20):
            batch=",".join(res[i:i+20])
            mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"catalog_product_id"},timeout=20).json()
            for x in mg:
                if x.get("code")==200:
                    cp=(x["body"] or {}).get("catalog_product_id")
                    if cp: existing_cpids.add(cp)
        if len(res)<50 or off>1500: break
        off+=50
print(f"Adrián existing CPIDs: {len(existing_cpids)}")

# Batch 1 — 5 perfumes objetivo
TARGETS=[
  {"q":"Armaf Club De Nuit Maleka","size":"105 ml"},
  {"q":"Emporio Armani Stronger With You","size":"100 ml"},
  {"q":"Initio Oud For Greatness","size":"90 ml"},
  {"q":"Armaf Lions Club Rugir","size":"100 ml"},
  {"q":"Al Haramain Amber Oud Ruby Edition","size":"100 ml"},
]

def find_best_cpid(query, target_size):
    """Buscar CPIDs matching query, excluir 200ml, preferir target_size."""
    r=requests.get(f"{API}/products/search",headers=H,params={"site_id":"MLM","q":query,"status":"active","limit":15},timeout=20).json()
    candidates=[]
    for p in (r.get("results") or []):
        cpid=p.get("id")
        name=(p.get("name") or "")
        lower=name.lower()
        if "200 ml" in lower or "200ml" in lower: continue
        # priority score
        sc=0
        if target_size.replace(" ","") in lower.replace(" ",""): sc+=10
        if all(w in lower for w in query.lower().split()[:3]): sc+=5
        candidates.append((sc,cpid,name))
    candidates.sort(key=lambda x:-x[0])
    return candidates[:5]  # return top 5 for inspection

print("\n=== SEARCH per perfume ===")
plan=[]
for t in TARGETS:
    cands=find_best_cpid(t["q"],t["size"])
    print(f"\n[{t['q']}] target={t['size']}")
    if not cands:
        print(f"  → NO CANDIDATES")
        plan.append((t,None))
        continue
    for sc,cp,name in cands[:3]:
        flag="✓" if cp not in existing_cpids else "(already in Adrián)"
        print(f"  sc={sc} {cp} {flag} | {name[:75]}")
    # Pick best not-already
    pick=next((c for c in cands if c[1] not in existing_cpids),None)
    plan.append((t,pick))

# Publish each pick
print("\n=== PUBLISH ===")
results={"ok":[],"skip":[],"fail":[]}
for t,pick in plan:
    if not pick:
        results["skip"].append((t["q"],"sin_candidato_o_todos_dup"))
        print(f"SKIP {t['q']} — sin candidato disponible")
        continue
    sc,cpid,name=pick
    # Buy-box price
    pr=requests.get(f"{API}/products/{cpid}",headers=H,timeout=15).json()
    bb=pr.get("buy_box_winner") or {}
    price=bb.get("price") or 999
    # category from buy-box winner item
    cat=None
    if bb.get("item_id"):
        tmp=requests.get(f"{API}/items/{bb['item_id']}",headers=H,params={"attributes":"category_id"},timeout=10).json()
        cat=tmp.get("category_id")
    if not cat:
        # fallback category for perfumes
        cat="MLM177562"
    payload={
        "site_id":"MLM","category_id":cat,
        "price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now",
        "listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":cpid,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True}
    }
    r=requests.post(f"{API}/items",headers=HJ,json=payload,timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        results["ok"].append((t["q"],cpid,d["id"],d.get("status"),d.get("price"),name))
        print(f"OK {t['q']} → cpid={cpid} new_id={d['id']} status={d.get('status')} ${d.get('price')}")
    else:
        results["fail"].append((t["q"],cpid,r.status_code,r.text[:250]))
        print(f"FAIL {t['q']} cpid={cpid} {r.status_code} {r.text[:250]}")
    time.sleep(1.2)

print(f"\n=== RESUMEN === ok={len(results['ok'])} skip={len(results['skip'])} fail={len(results['fail'])}")
print("\n--- LINKS ---")
for q,cpid,iid,st,pr,name in results["ok"]:
    print(f"\n{q}")
    print(f"  catalog CPID: {cpid}")
    print(f"  new listing: MLM{iid.replace('MLM','')}")
    print(f"  $ {pr} | {st}")
    print(f"  name: {name[:80]}")
