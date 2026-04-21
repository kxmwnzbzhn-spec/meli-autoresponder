import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
sid=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()["id"]
ids=[]; s=0
while True:
    d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?limit=100&offset={s}",headers=H).json()
    got=d.get("results",[])
    if not got: break
    ids+=got; s+=100
    if s>=d.get("paging",{}).get("total",0): break
# incluir closed tmb
for st in ["closed","paused","under_review","inactive"]:
    s=0
    while True:
        d=requests.get(f"https://api.mercadolibre.com/users/{sid}/items/search?status={st}&limit=100&offset={s}",headers=H).json()
        got=d.get("results",[])
        if not got: break
        for i in got:
            if i not in ids: ids.append(i)
        s+=100
        if s>=d.get("paging",{}).get("total",0): break
print(f"total items: {len(ids)}")
bocinas=[]
for i in range(0,len(ids),20):
    b=",".join(ids[i:i+20])
    res=requests.get(f"https://api.mercadolibre.com/items?ids={b}&attributes=id,title,status,sub_status,catalog_listing,catalog_product_id,price",headers=H).json()
    for x in res:
        b2=x.get("body",{})
        t=(b2.get("title") or "").lower()
        if any(k in t for k in ["jbl","sony srs","bocina","parlante","altavoz"]):
            bocinas.append(b2)
# Solo activas
active=[b for b in bocinas if b.get("status")=="active"]
# Clasificar
def classify(t):
    t=t.lower()
    model="?"; color="?"
    if "charge 6" in t or "charge6" in t: model="Charge 6"
    elif "flip 7" in t or "flip7" in t: model="Flip 7"
    elif "clip 5" in t or "clip5" in t: model="Clip 5"
    elif "grip" in t: model="Grip"
    elif "go essential" in t or "goessential" in t or "go-essential" in t: model="Go Essential 2"
    elif "go 4" in t or "go4" in t: model="Go 4"
    elif "go 3" in t or "go3" in t: model="Go 3"
    elif "srs-xb100" in t or "xb100" in t: model="Sony XB100"
    for c in ["negra","negro","azul marino","azul","roja","rojo","rosa","morada","morado","violeta","camuflaje","camo","blanco","blanca","verde","naranja"]:
        if c in t:
            # normalizar
            norm={"negro":"Negra","negra":"Negra","azul":"Azul","azul marino":"Azul Marino","roja":"Roja","rojo":"Roja","rosa":"Rosa","morado":"Morada","morada":"Morada","violeta":"Morada","camuflaje":"Camuflaje","camo":"Camuflaje","blanco":"Blanca","blanca":"Blanca"}
            color=norm.get(c,c.title()); break
    return model,color
# Inventario real deseado
EXPECTED = {
    ("Charge 6","Azul"), ("Charge 6","Roja"), ("Charge 6","Camuflaje"),
    ("Flip 7","Negra"), ("Flip 7","Roja"), ("Flip 7","Morada"),
    ("Clip 5","Negra"), ("Clip 5","Morada"), ("Clip 5","Rosa"),
    ("Grip","Negra"),
    ("Sony XB100","Negra"),
    ("Go Essential 2","Azul"), ("Go Essential 2","Roja"),
    ("Go 4","Negra"), ("Go 4","Roja"), ("Go 4","Rosa"), ("Go 4","Azul Marino"), ("Go 4","Camuflaje"),
    ("Go 3","Negra"),
}
found={}
for b in active:
    m,c=classify(b.get("title") or "")
    if (m,c) not in found:
        found[(m,c)]=[]
    found[(m,c)].append(b)

print("\n=== BOCINAS ACTIVAS ===")
for b in active:
    m,c=classify(b.get("title") or "")
    clist="catálogo" if b.get("catalog_listing") else "tradicional"
    print(f"  {b.get('id')} | {m:<16} {c:<14} ${b.get('price'):<5} | {clist} | {b.get('title')[:60]}")

print("\n=== COBERTURA ===")
total_ok=0
missing=[]
for mc in sorted(EXPECTED):
    fs=found.get(mc,[])
    if fs:
        total_ok+=1
        # Lista IDs
        ids_s=", ".join(x["id"] for x in fs)
        print(f"  OK  {mc[0]:<16} {mc[1]:<14} [{len(fs)}x] {ids_s}")
    else:
        missing.append(mc)
        print(f"  ❌  {mc[0]:<16} {mc[1]:<14} FALTA")

print(f"\nCubiertas: {total_ok}/{len(EXPECTED)}")
print(f"Faltantes: {len(missing)}")
