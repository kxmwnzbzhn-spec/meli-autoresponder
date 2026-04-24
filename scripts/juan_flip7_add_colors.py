import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

IID="MLM2887824025"
# Buscar items live JBL Flip 7 Rojo y Morado
MISSING={"Rojo":[],"Morado":[]}

for color in list(MISSING.keys()):
    for q in [f"JBL Flip 7 {color}", f"Bocina JBL Flip 7 {color}", f"JBL Flip {color}"]:
        s=requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q={q}&category=MLM59800&limit=20&condition=new",headers=H).json()
        for r_ in (s.get("results") or [])[:20]:
            t=r_.get("title","")
            if "Flip 7" not in t or "JBL" not in t: continue
            iid=r_.get("id")
            d=requests.get(f"https://api.mercadolibre.com/items/{iid}?attributes=pictures,attributes,title",headers=H).json()
            ic=None
            for a in (d.get("attributes") or []):
                if a.get("id")=="COLOR": ic=a.get("value_name"); break
            if ic==color or color.lower() in t.lower():
                urls=[x.get("url") for x in (d.get("pictures") or []) if x.get("url")][:4]
                if urls:
                    MISSING[color]=urls
                    print(f"  {color}: {len(urls)} pics from {iid}")
                    break
        if MISSING[color]: break

# Upload
def upload(url):
    try:
        img=requests.get(url,timeout=20).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOKEN}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

new_ids={}
for color,urls in MISSING.items():
    ids=[]
    for u in urls:
        pid=upload(u)
        if pid: ids.append(pid)
    new_ids[color]=ids
    print(f"  uploaded {color}: {len(ids)}")

# Obtener estado actual del item y añadir variations
cur=requests.get(f"https://api.mercadolibre.com/items/{IID}?include_attributes=all",headers=H).json()
current_vars=cur.get("variations",[])
print(f"\nVariaciones actuales: {len(current_vars)}")
for v in current_vars:
    color=None
    for ac in v.get("attribute_combinations",[]): 
        if ac.get("id")=="COLOR": color=ac.get("value_name"); break
    print(f"  {color}: {v.get('id')}")

# Preservar existentes + agregar nuevas
GTIN_PER_COLOR={"Rojo":"1200130019296","Morado":"1200130019319"}
new_vars=list(current_vars)  # keep existing
for color in ["Rojo","Morado"]:
    if new_ids.get(color):
        new_vars.append({
            "price":799,"available_quantity":10,
            "attribute_combinations":[{"id":"COLOR","value_name":color}],
            "attributes":[{"id":"GTIN","value_name":GTIN_PER_COLOR[color]}],
            "picture_ids":new_ids[color],
        })
# Recopilar todas las pics
all_pics=[]
for p in (cur.get("pictures") or []):
    if p.get("id") and p.get("id") not in all_pics: all_pics.append(p.get("id"))
for ids in new_ids.values():
    for p in ids:
        if p not in all_pics: all_pics.append(p)

body={
    "pictures":[{"id":p} for p in all_pics],
    "variations":new_vars,
}
print(f"\n=== PUT agregar Rojo+Morado ===")
rp=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body,timeout=60)
print(f"status: {rp.status_code}")
if rp.status_code not in (200,201):
    print(rp.text[:1000])
else:
    print("*** Variaciones actualizadas ***")
