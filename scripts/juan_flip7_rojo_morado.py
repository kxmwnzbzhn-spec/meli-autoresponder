import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

IID="MLM2887824025"

# Buscar items live en MELI con Flip 7 Rojo y Morado (cualquier seller)
print("=== BUSCAR PICS EN ITEMS LIVE ===")
MISSING={"Rojo":[],"Morado":[]}
queries={
    "Rojo":["JBL Flip 7 Rojo","Parlante JBL Flip 7 Rojo","Bocina JBL Flip7 Rojo","JBL FLIP7REDAM"],
    "Morado":["JBL Flip 7 Morado","JBL Flip 7 Purpura","Parlante JBL Flip 7 Morado","JBL Flip 7 Purple","JBL Flip 7 Violeta"],
}
for color,qs in queries.items():
    for q in qs:
        if MISSING[color]: break
        s=requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={q}&category=MLM59800&limit=20",headers=H,timeout=15).json()
        for r_ in (s.get("results") or [])[:20]:
            t=r_.get("title","").lower()
            if "flip 7" not in t and "flip7" not in t: continue
            iid=r_.get("id")
            d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=pictures,attributes,title",headers=H,timeout=10).json()
            ic=None
            for a in (d.get("attributes") or []):
                if a.get("id")=="COLOR": ic=(a.get("value_name") or "").lower(); break
            if ic==color.lower() or color.lower() in t or (color=="Morado" and ("morado" in t or "purpl" in t or "violet" in t)):
                urls=[x.get("url") for x in (d.get("pictures") or []) if x.get("url")][:4]
                if urls:
                    MISSING[color]=urls
                    print(f"  {color}: {len(urls)} pics from {iid} ('{d.get('title','')[:50]}')")
                    break

# Tambien probar catalog products Flip 7 Rojo/Morado conocidos (hallados antes)
# MLM48958711 = "Parlante Portatil Jbl Flip 7 Rojo" COLOR=Rojo pics=5
# MLM50260512 = "Altavoz Bluetooth Jbl Flip 7 rosa" COLOR=Rosa pics=5 (NO Morado)
if not MISSING["Rojo"]:
    p=requests.get(f"https://api.mercadolibre.com/products/MLM48958711",headers=H).json()
    urls=[x.get("url") for x in (p.get("pictures") or []) if x.get("url")][:5]
    if urls:
        MISSING["Rojo"]=urls
        print(f"  Rojo desde catalog MLM48958711: {len(urls)} pics")

# Subir a Juan
def upload(url):
    try:
        img=requests.get(url,timeout=20).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

new_ids={"Rojo":[],"Morado":[]}
for color,urls in MISSING.items():
    for u in urls[:4]:
        pid=upload(u)
        if pid: new_ids[color].append(pid)
    print(f"  uploaded {color}: {len(new_ids[color])}")

# Obtener item actual y agregar variations
cur=requests.get(f"https://api.mercadolibre.com/items/{IID}?include_attributes=all",headers=H).json()
print(f"\nVariaciones actuales: {len(cur.get('variations') or [])}")
current_vars=cur.get("variations",[])
for v in current_vars:
    col=None
    for ac in v.get("attribute_combinations",[]):
        if ac.get("id")=="COLOR": col=ac.get("value_name"); break
    print(f"  {col}: qty={v.get('available_quantity')}")

GTIN_PER_COLOR={"Rojo":"1200130019296","Morado":"1200130019319"}
new_vars=[]
# Preservar existentes (sin "id" porque MELI rechaza "id" al PUT variations)
for v in current_vars:
    nv={
        "price":v.get("price"),
        "available_quantity":v.get("available_quantity"),
        "attribute_combinations":v.get("attribute_combinations",[]),
        "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])],
    }
    # Preservar GTIN si estaba
    for a in (v.get("attributes") or []):
        if a.get("id")=="GTIN":
            nv["attributes"]=[{"id":"GTIN","value_name":a.get("value_name")}]
    new_vars.append(nv)

# Agregar Rojo y Morado
for color in ["Rojo","Morado"]:
    if new_ids.get(color):
        new_vars.append({
            "price":799,"available_quantity":10,
            "attribute_combinations":[{"id":"COLOR","value_name":color}],
            "attributes":[{"id":"GTIN","value_name":GTIN_PER_COLOR[color]}],
            "picture_ids":new_ids[color],
        })
        print(f"  +agregar {color}")
    else:
        print(f"  NO pics para {color}, skip")

# Collect all pics
all_pics=[]
for p in (cur.get("pictures") or []):
    pid=p.get("id")
    if pid and pid not in all_pics: all_pics.append(pid)
for ids in new_ids.values():
    for p in ids:
        if p not in all_pics: all_pics.append(p)

body={"pictures":[{"id":p} for p in all_pics],"variations":new_vars}
rp=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body,timeout=60)
print(f"\nupdate: {rp.status_code}")
if rp.status_code not in (200,201):
    print(rp.text[:1500])
else:
    print("*** Rojo y Morado agregados OK ***")
