import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}
UID=requests.get(f"{API}/users/me",headers=H,timeout=15).json()["id"]
print("ASVA uid:",UID)
def sec(t): print(f"\n=== {t} ===")
# 1) buscar listing Attessa / set seamless
sec("Buscar items ASVA: attessa / seamless / conjunto")
found=None
for q in ["attessa","set seamless escultural","conjunto deportivo seamless","set deportivo seamless","attessa sport","seamless escultural"]:
    r=requests.get(f"{API}/users/{UID}/items/search",params={"status":"active","q":q,"limit":10},headers=H,timeout=15)
    ids=r.json().get("results") or []
    print(f"q='{q}' -> {len(ids)}")
    for iid in ids:
        it=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
        tl=(it.get('title') or '')
        print(f"   {iid} | {tl[:70]} | dom={it.get('domain_id')}")
        if not found and ("seamless" in tl.lower() or "attessa" in tl.lower() or "escultural" in tl.lower() or it.get('domain_id')=="MLM-SPORTSWEAR_SETS"):
            found=it
    if found: break
if found:
    sec(f"DETALLE listing {found['id']}")
    print("title:",found.get("title"))
    print("domain:",found.get("domain_id"),"cat:",found.get("category_id"))
    print("price:",found.get("price"),"| variations:",len(found.get("variations") or []))
    print("pictures:",len(found.get("pictures") or []))
    print("ATRIBUTOS:")
    for a in found.get("attributes",[]):
        print(f"   [{a.get('id')}] {a.get('name')} = {a.get('value_name')}")
    if found.get("variations"):
        print("VARIACIONES:")
        for v in found["variations"][:8]:
            ats={x.get('name'):x.get('value_name') for x in v.get('attribute_combinations',[])}
            print(f"   var {v.get('id')}: {ats} | pics={len(v.get('picture_ids') or [])}")
else:
    print("No encontré listing Attessa en ASVA.")
# 2) technical specs required del dominio
sec("technical_specs MLM-SPORTSWEAR_SETS (required)")
r=requests.get(f"{API}/domains/MLM-SPORTSWEAR_SETS/technical_specs",headers=H,timeout=20)
print("status",r.status_code)
if r.status_code==200:
    def walk(n):
        if isinstance(n,dict):
            if n.get("id") and ("tags" in n or "values" in n or "value_type" in n):
                tg=[k for k,v in (n.get("tags",{}) or {}).items() if v]
                if "required" in tg or "catalog_required" in tg:
                    vals=", ".join(x.get("name","?") for x in (n.get("values") or [])[:6])
                    print(f"   REQ [{n.get('id')}] {n.get('name')} {('| '+vals) if vals else ''}")
            for v in n.values(): walk(v)
        elif isinstance(n,list):
            for v in n: walk(v)
    walk(r.json())
