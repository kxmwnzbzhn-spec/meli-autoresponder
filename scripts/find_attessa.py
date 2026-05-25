import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}
UID=requests.get(f"{API}/users/me",headers=H,timeout=15).json()["id"]
print("ASVA uid:",UID)
seen=set()
def show(iid):
    if iid in seen: return
    seen.add(iid)
    it=requests.get(f"{API}/items/{iid}",headers=H,timeout=10).json()
    print(f"  {iid} | {it.get('status')}/{it.get('sub_status')} | {(it.get('title') or '')[:65]} | dom={it.get('domain_id')} | cat={it.get('category_id')}")

# A) búsqueda por keywords sin filtrar status
print("\n[A] por keywords (todos estados)")
for q in ["seamless","escultural","conjunto deportivo","set deportivo","leggings","attessa","ropa deportiva","conjunto mujer"]:
    r=requests.get(f"{API}/users/{UID}/items/search",params={"q":q,"limit":15},headers=H,timeout=15)
    ids=r.json().get("results") or []
    if ids: print(f" q='{q}' -> {len(ids)}")
    for iid in ids[:10]: show(iid)

# B) por categoría conjuntos deportivos
print("\n[B] por categoría sportswear")
for cat in ["MLM429750","MLM429215","MLM438514"]:
    r=requests.get(f"{API}/users/{UID}/items/search",params={"category":cat,"limit":20},headers=H,timeout=15)
    ids=r.json().get("results") or []
    print(f" cat={cat} -> {len(ids)}")
    for iid in ids[:10]: show(iid)

# C) cuántos items totales tiene ASVA
r=requests.get(f"{API}/users/{UID}/items/search",params={"limit":1},headers=H,timeout=15)
print("\nTotal items ASVA:",r.json().get("paging",{}).get("total"))
