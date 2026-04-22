import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
sid=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()["id"]

# Traer TODOS los items (cualquier status)
ids=[]
for st in ["active","paused","closed","under_review","inactive"]:
    s=0
    while True:
        d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status={st}&limit=100&offset={s}",headers=H,timeout=20).json()
        got=d.get("results",[])
        if not got: break
        for i in got:
            if i not in ids: ids.append(i)
        s+=100
        if s>=d.get("paging",{}).get("total",0): break
# tambien sin status filter por UNDER_REVIEW_ACCREDITATION_REQUIRED
s=0
while True:
    d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?filters=UNDER_REVIEW_ACCREDITATION_REQUIRED&limit=100&offset={s}",headers=H,timeout=20).json()
    got=d.get("results",[])
    if not got: break
    for i in got:
        if i not in ids: ids.append(i)
    s+=100
    if s>=d.get("paging",{}).get("total",0): break

print(f"Total items: {len(ids)}")

# Obtener detalles batch
items_data=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    res=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,price,status,sub_status,catalog_product_id,category_id,condition,listing_type_id,available_quantity,pictures,attributes",headers=H,timeout=30).json()
    for x in res:
        b=x.get("body",{})
        if b:
            items_data.append(b)

# Clasificar perfumes vs bocinas
perfumes=[]
bocinas=[]
for it in items_data:
    title=(it.get("title") or "").lower()
    cat=it.get("category_id","")
    if cat.startswith("MLM1271") or any(k in title for k in ["perfume","edp","eau de","parfum"]):
        perfumes.append(it)
    elif any(k in title for k in ["jbl","sony srs","bocina","parlante","altavoz","speaker","bose"]):
        bocinas.append(it)

print(f"Perfumes: {len(perfumes)}")
print(f"Bocinas: {len(bocinas)}")

# Guardar listados
with open("juan_perfumes.json","w") as f: json.dump(perfumes,f,indent=1,ensure_ascii=False)
with open("juan_bocinas.json","w") as f: json.dump(bocinas,f,indent=1,ensure_ascii=False)

# Resumen
print("\n=== PERFUMES ===")
for p in perfumes[:50]:
    print(f"  {p.get('id')} ${p.get('price')} | {p.get('title','')[:70]}")
print(f"\n=== BOCINAS ===")
for b in bocinas:
    print(f"  {b.get('id')} ${b.get('price')} | {b.get('title','')[:70]}")
