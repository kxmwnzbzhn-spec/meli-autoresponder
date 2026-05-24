import os, requests
import meli_token
API="https://api.mercadolibre.com"
at=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"]).json()["access_token"]
H={"Authorization":f"Bearer {at}"}
uid=1668713481
ids=[]; off=0
for st in ("active","paused"):
    off=0
    while True:
        j=requests.get(f"{API}/users/{uid}/items/search?status={st}&limit=100&offset={off}",headers=H,timeout=20).json()
        r=j.get("results",[]); ids+=r; off+=100
        if off>=j.get("paging",{}).get("total",0) or not r: break
print("total items ASVA:",len(ids))
hits=[]
for i in range(0,len(ids),20):
    r=requests.get(f"{API}/items?ids={','.join(ids[i:i+20])}&attributes=id,title,price,available_quantity,status,catalog_product_id,domain_id,category_id",headers=H,timeout=25).json()
    for it in r:
        b=it.get("body",{})
        t=(b.get("title") or "").lower(); dom=(b.get("domain_id") or "")
        if "HEADPHONE" in dom.upper() or any(k in t for k in ["audif","auricul","buds","headphone","earbud","diadema"]):
            hits.append(b)
print("headphones encontrados:",len(hits))
for b in hits:
    print(f"  {b.get('id')} ${b.get('price')} q={b.get('available_quantity')} {b.get('status')} dom={b.get('domain_id')} cpid={b.get('catalog_product_id')} :: {b.get('title')[:60]}")
print("DONE")
