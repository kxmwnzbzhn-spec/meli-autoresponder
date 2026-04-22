import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_OFICIAL"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
sid=me.get("id")
print(f"Cuenta: {me.get('nickname')} id={sid}")

# Traer todos los items bajo review
ids=[]
for st in ["under_review","paused","active","inactive"]:
    s=0
    while True:
        d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status={st}&limit=100&offset={s}",headers=H,timeout=20).json()
        got=d.get("results",[])
        if not got: break
        for i in got:
            if i not in ids: ids.append(i)
        s+=100
        if s>=d.get("paging",{}).get("total",0): break

# Tambien con filter UNDER_REVIEW_ACCREDITATION_REQUIRED
for flt in ["UNDER_REVIEW_ACCREDITATION_REQUIRED","UNDER_REVIEW","PENDING_DOCUMENTATION"]:
    s=0
    while True:
        d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?filters={flt}&limit=100&offset={s}",headers=H,timeout=20).json()
        got=d.get("results",[])
        if not got: break
        for i in got:
            if i not in ids: ids.append(i)
        s+=100
        if s>=d.get("paging",{}).get("total",0): break

print(f"Total items: {len(ids)}")

# Detalles y filtrar los que piden factura
need_factura=[]
for i in range(0,len(ids),20):
    batch=",".join(ids[i:i+20])
    res=requests.get(f"https://api.mercadolibre.com/items?ids={batch}&attributes=id,title,price,status,sub_status",headers=H,timeout=20).json()
    for x in res:
        b=x.get("body",{})
        if not b: continue
        ss=b.get("sub_status") or []
        ss_str=",".join(ss) if isinstance(ss,list) else str(ss)
        # flags que indican necesita factura/documentación
        if any(tag in ss_str.lower() for tag in ["pending_documentation","accreditation_required","waiting_for_documentation","documentation"]):
            need_factura.append({"id":b.get("id"),"title":b.get("title",""),"price":b.get("price"),"status":b.get("status"),"ss":ss_str})

print(f"\n=== PIDEN FACTURA: {len(need_factura)} ===\n")
# Agrupar por tipo
perfumes=[]
bocinas=[]
otros=[]
for n in need_factura:
    t=(n.get("title") or "").lower()
    if any(k in t for k in ["perfume","edp","eau de","parfum"]):
        perfumes.append(n)
    elif any(k in t for k in ["jbl","bocina","parlante","altavoz","sony"]):
        bocinas.append(n)
    else:
        otros.append(n)

print(f"\n--- PERFUMES ({len(perfumes)}) ---")
for p in perfumes:
    print(f"  {p['id']} ${p['price']} | {p['title'][:70]}")

print(f"\n--- BOCINAS ({len(bocinas)}) ---")
for b in bocinas:
    print(f"  {b['id']} ${b['price']} | {b['title'][:70]}")

if otros:
    print(f"\n--- OTROS ({len(otros)}) ---")
    for o in otros:
        print(f"  {o['id']} ${o['price']} | {o['title'][:70]}")

# Save as md for copy-paste
with open("claribel_piden_factura.md","w") as f:
    f.write(f"# Publicaciones Claribel que piden factura\n\nCuenta: CX20260420180750 (id {sid})\nTotal: {len(need_factura)} items\n\n")
    f.write(f"## Perfumes ({len(perfumes)})\n\n")
    for p in perfumes:
        f.write(f"- **{p['id']}** — ${p['price']} — {p['title']}\n")
    f.write(f"\n## Bocinas ({len(bocinas)})\n\n")
    for b in bocinas:
        f.write(f"- **{b['id']}** — ${b['price']} — {b['title']}\n")
    if otros:
        f.write(f"\n## Otros ({len(otros)})\n\n")
        for o in otros:
            f.write(f"- **{o['id']}** — ${o['price']} — {o['title']}\n")
print(f"\nGuardado: claribel_piden_factura.md")
