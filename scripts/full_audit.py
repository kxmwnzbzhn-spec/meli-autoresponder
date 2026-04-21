import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
sid=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()["id"]
# Traer TODOS los items sin filtro de status
ids=[]; s=0
while True:
    d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?limit=100&offset={s}&include_filters=false",headers=H).json()
    got=d.get("results",[])
    if not got: break
    ids+=got; s+=100
    if s>=d.get("paging",{}).get("total",0): break
# Tambien con filters especiales
for f in ["UNDER_REVIEW_ACCREDITATION_REQUIRED","UNDER_REVIEW","PENDING_DOCUMENTATION","FORBIDDEN"]:
    s=0
    while True:
        d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?limit=100&offset={s}&filters={f}",headers=H).json()
        got=d.get("results",[])
        if not got: break
        for i in got:
            if i not in ids: ids.append(i)
        s+=100
        if s>=d.get("paging",{}).get("total",0): break
# Tambien por status explicit
for st in ["closed","paused","under_review","inactive","active"]:
    s=0
    while True:
        d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status={st}&limit=100&offset={s}",headers=H).json()
        got=d.get("results",[])
        if not got: break
        for i in got:
            if i not in ids: ids.append(i)
        s+=100
        if s>=d.get("paging",{}).get("total",0): break

print(f"Total items encontrados: {len(ids)}")

bocinas=[]
for i in range(0,len(ids),20):
    b=",".join(ids[i:i+20])
    res=requests.get(f"https://api.mercadolibre.com/items?ids={b}&attributes=id,title,status,sub_status,catalog_listing,catalog_product_id,price,date_created",headers=H).json()
    for x in res:
        b2=x.get("body",{})
        t=(b2.get("title") or "").lower()
        if any(k in t for k in ["jbl","sony srs","bocina","parlante","altavoz","speaker"]):
            bocinas.append(b2)

print(f"\nBocinas encontradas: {len(bocinas)}")

def norm_sub(s):
    if isinstance(s,list): return ",".join(s) or "-"
    return s or "-"

# Organizar por modelo+color
def classify(t):
    t=t.lower()
    model="OTRO"; color="?"
    if "charge 6" in t or "charge6" in t: model="Charge 6"
    elif "flip 7" in t or "flip7" in t: model="Flip 7"
    elif "clip 5" in t or "clip5" in t: model="Clip 5"
    elif "grip" in t: model="Grip"
    elif "go essential" in t or "goessential" in t: model="Go Essential 2"
    elif "go 4" in t or "go4" in t: model="Go 4"
    elif "go 3" in t or "go3" in t: model="Go 3"
    elif "srs-xb100" in t or "xb100" in t or "sony srs" in t: model="Sony XB100"
    for raw,norm in [("azul marino","Azul Marino"),("camuflaje","Camuflaje"),("camo","Camuflaje"),("morado","Morada"),("morada","Morada"),("violeta","Morada"),("purple","Morada"),("negra","Negra"),("negro","Negra"),("black","Negra"),("azul","Azul"),("blue","Azul"),("roja","Roja"),("rojo","Roja"),("red","Roja"),("rosa","Rosa"),("pink","Rosa"),("blanca","Blanca"),("blanco","Blanca"),("white","Blanca"),("naranja","Naranja"),("verde","Verde")]:
        if raw in t: color=norm; break
    return model,color

# imprimir TODAS organizadas
by_key={}
for b in bocinas:
    m,c=classify(b.get("title") or "")
    k=(m,c)
    by_key.setdefault(k,[]).append(b)

print("\n=== INVENTARIO COMPLETO (TODAS las bocinas, todos estados) ===")
EXPECTED=[
    ("Charge 6","Azul"),("Charge 6","Roja"),("Charge 6","Camuflaje"),
    ("Flip 7","Negra"),("Flip 7","Roja"),("Flip 7","Morada"),
    ("Clip 5","Negra"),("Clip 5","Morada"),("Clip 5","Rosa"),
    ("Grip","Negra"),
    ("Sony XB100","Negra"),
    ("Go Essential 2","Azul"),("Go Essential 2","Roja"),
    ("Go 4","Negra"),("Go 4","Roja"),("Go 4","Rosa"),("Go 4","Azul Marino"),("Go 4","Camuflaje"),
    ("Go 3","Negra"),
]
print(f"\n{'MODELO':<16} {'COLOR':<14} {'ACTIVA':<7} {'UNDER_REV':<10} {'CLOSED':<7} {'OTHER':<6} IDs")
for k in EXPECTED:
    items=by_key.get(k,[])
    active=[b for b in items if b.get("status")=="active"]
    rev=[b for b in items if b.get("status")=="under_review"]
    closed=[b for b in items if b.get("status") in ("closed","inactive")]
    other=[b for b in items if b.get("status") not in ("active","under_review","closed","inactive")]
    status_sum=f"{len(active):<7} {len(rev):<10} {len(closed):<7} {len(other):<6}"
    # ids con status
    ids_s=[]
    for b in items:
        s=b.get("status")[:4]
        ss=norm_sub(b.get("sub_status"))[:12]
        ids_s.append(f"{b.get('id')}({s}/{ss})")
    print(f"{k[0]:<16} {k[1]:<14} {status_sum}  {', '.join(ids_s) if ids_s else 'NINGUNO'}")

# Tambien otras bocinas no esperadas
print("\n=== OTRAS BOCINAS NO ESPERADAS ===")
for k,items in sorted(by_key.items()):
    if k in EXPECTED: continue
    for b in items:
        print(f"  {b.get('id')} | {b.get('status')}/{norm_sub(b.get('sub_status'))} | ${b.get('price')} | {k[0]}/{k[1]} | {b.get('title')[:70]}")

print("\n=== RESUMEN ===")
total_active=sum(1 for k in EXPECTED if any(b.get("status")=="active" for b in by_key.get(k,[])))
total_pending=sum(1 for k in EXPECTED if not any(b.get("status")=="active" for b in by_key.get(k,[])) and any(b.get("status")=="under_review" for b in by_key.get(k,[])))
total_sin_nada=sum(1 for k in EXPECTED if not any(b.get("status") in ("active","under_review") for b in by_key.get(k,[])))
print(f"  Activas (vendiéndose): {total_active}/19")
print(f"  Solo under_review (esperando factura): {total_pending}/19")
print(f"  Sin publicación activa ni en revisión: {total_sin_nada}/19")
