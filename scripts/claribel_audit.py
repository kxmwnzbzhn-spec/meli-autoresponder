import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]}).json()
if "access_token" not in r:
    print(f"!!! REFRESH FAIL: {r}")
    exit(1)
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
print(f"Claribel: {me.get('nickname')} ({me.get('id')})")
USER_ID=me["id"]

# Listar todos items
all_items=[]
for status in ("active","paused","closed"):
    offset=0
    while True:
        s=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status={status}&limit=100&offset={offset}",headers=H,timeout=20).json()
        items=s.get("results") or []
        all_items.extend([(iid,status) for iid in items])
        total=s.get("paging",{}).get("total",0)
        offset+=100
        if offset>=total or not items: break
print(f"Total items: {len(all_items)}")

# Clasificar por tipo
perfumes=[]
speakers=[]
others=[]
for iid,st in all_items:
    d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=id,title,category_id,status,price",headers=H,timeout=10).json()
    t=d.get("title","").lower()
    cat=d.get("category_id","")
    is_perfume = any(k in t for k in ["perfume","edp","edt","fragancia","eau de"]) or cat in ("MLM3475","MLM405398","MLM436275")
    is_speaker = "bocina" in t or "altavoz" in t or "speaker" in t or "parlante" in t or cat=="MLM59800"
    info={"id":iid,"title":d.get('title',''),"cat":cat,"status":d.get('status'),"price":d.get('price')}
    if is_perfume:
        perfumes.append(info)
    elif is_speaker:
        speakers.append(info)
    else:
        others.append(info)
print(f"\nPerfumes: {len(perfumes)}")
print(f"Bocinas: {len(speakers)}")
print(f"Otros: {len(others)}")

print("\n=== BOCINAS (se cerrarán todas) ===")
for s in speakers[:30]:
    print(f"  {s['id']} [{s['status']}] ${s['price']}: {s['title'][:60]}")

print("\n=== OTROS (se cerrarán) ===")
for o in others[:30]:
    print(f"  {o['id']} [{o['status']}] ${o['price']}: {o['title'][:60]} ({o['cat']})")

print("\n=== PERFUMES (se conservan) ===")
for p in perfumes[:30]:
    print(f"  {p['id']} [{p['status']}] ${p['price']}: {p['title'][:60]}")

# Guardar clasificación para el siguiente paso
with open("claribel_inventory.json","w") as f:
    json.dump({"perfumes":perfumes,"speakers":speakers,"others":others},f,indent=2,ensure_ascii=False)
