import os, re, json, unicodedata, requests
from collections import defaultdict
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token",
    "client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],
    "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
H={"Authorization":f"Bearer {T}"}
me=requests.get(f"{API}/users/me",headers=H,timeout=20).json()
UID=me["id"]
print(f"seller_id={UID} nick={me.get('nickname')}")

# Listar TODOS los IDs activos
ids=[]
scroll=None
while True:
    p={"search_type":"scan","limit":100,"status":"active"}
    if scroll: p["scroll_id"]=scroll
    r=requests.get(f"{API}/users/{UID}/items/search",headers=H,params=p,timeout=30).json()
    if "results" not in r: print("ERR",r); break
    ids+=r["results"]
    scroll=r.get("scroll_id")
    if not scroll or not r["results"]: break
print(f"total_active_ids={len(ids)}")

# multiget en bloques de 20
items=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    r=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,title,price,available_quantity,sold_quantity,catalog_product_id,catalog_listing,category_id,variations,date_created,permalink,status,health"},timeout=30).json()
    for x in r:
        if x.get("code")==200:
            items.append(x["body"])
print(f"loaded={len(items)}")

def norm(s):
    s=(s or "").lower()
    s=unicodedata.normalize("NFD",s)
    s="".join(c for c in s if unicodedata.category(c)!="Mn")
    s=re.sub(r"[^a-z0-9 ]+"," ",s)
    s=re.sub(r"\s+"," ",s).strip()
    # quitar stopwords ruidosos
    drop={"bocina","bocinas","altavoz","parlante","portatil","portátil","bluetooth","con","de","la","el","y","color","colores","jbl","sony","bose","waterproof","impermeable","ip67","ip68"}
    return " ".join(w for w in s.split() if w not in drop)

# Agrupar por catalog_product_id y por título normalizado
by_cpid=defaultdict(list)
by_norm=defaultdict(list)
for it in items:
    cp=it.get("catalog_product_id")
    if cp: by_cpid[cp].append(it)
    n=norm(it.get("title",""))
    by_norm[n].append(it)

print("\n========== DUPLICADOS POR CATALOG_PRODUCT_ID ==========")
for cp,lst in sorted(by_cpid.items(),key=lambda x:-len(x[1])):
    if len(lst)<2: continue
    print(f"\nCPID {cp} ({len(lst)} listings):")
    for it in sorted(lst,key=lambda x:(-(x.get('sold_quantity') or 0),-(x.get('available_quantity') or 0))):
        print(f"  {it['id']} sold={it.get('sold_quantity'):>3} qty={it.get('available_quantity'):>3} ${it.get('price'):>6} cat={it.get('catalog_listing')} | {it.get('title','')[:80]}")

print("\n========== DUPLICADOS POR TITULO NORMALIZADO ==========")
shown=0
for n,lst in sorted(by_norm.items(),key=lambda x:-len(x[1])):
    if len(lst)<2: continue
    # evitar mostrar grupos donde TODOS ya están agrupados por cpid igual
    cps={(it.get('catalog_product_id') or '') for it in lst}
    if len(cps)==1 and "" not in cps: continue  # ya cubierto arriba
    shown+=1
    print(f"\nNORM '{n}' ({len(lst)} listings):")
    for it in sorted(lst,key=lambda x:(-(x.get('sold_quantity') or 0),-(x.get('available_quantity') or 0))):
        cp=it.get('catalog_product_id') or '-'
        print(f"  {it['id']} sold={it.get('sold_quantity'):>3} qty={it.get('available_quantity'):>3} ${it.get('price'):>6} cpid={cp:<14} | {it.get('title','')[:80]}")
    if shown>=40: break

# JSON resumen al final para parsear
print("\n===JSON===")
groups=[]
for cp,lst in by_cpid.items():
    if len(lst)>=2:
        groups.append({"key":f"cpid:{cp}","items":[{"id":i["id"],"title":i.get("title"),"price":i.get("price"),"qty":i.get("available_quantity"),"sold":i.get("sold_quantity"),"cpid":i.get("catalog_product_id"),"cat_listing":i.get("catalog_listing")} for i in lst]})
for n,lst in by_norm.items():
    if len(lst)<2: continue
    cps={(it.get('catalog_product_id') or '') for it in lst}
    if len(cps)==1 and "" not in cps: continue
    groups.append({"key":f"norm:{n}","items":[{"id":i["id"],"title":i.get("title"),"price":i.get("price"),"qty":i.get("available_quantity"),"sold":i.get("sold_quantity"),"cpid":i.get("catalog_product_id"),"cat_listing":i.get("catalog_listing")} for i in lst]})
print(json.dumps(groups,ensure_ascii=False))
