import os,requests,json,time

def get_token(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()["access_token"]

# Juan token — usamos solo para descubrir catalog children y pics por color
AT_J=get_token(os.environ["MELI_REFRESH_TOKEN"])
HJ={"Authorization":f"Bearer {AT_J}","Content-Type":"application/json"}

# 1) Obtener children del catalog Go 4 MLM64277114 con su color
parent=requests.get("https://api.mercadolibre.com/products/MLM64277114",headers=HJ).json()
children=parent.get("children_ids") or []
print(f"Catalog Go 4 MLM64277114 children: {children}")
color_to_cpid={}
for cid in children:
    d=requests.get(f"https://api.mercadolibre.com/products/{cid}",headers=HJ).json()
    color=None
    for a in (d.get("attributes") or []):
        if a.get("id")=="COLOR": color=a.get("value_name"); break
    color_to_cpid[color]=cid
    print(f"  {cid}: {d.get('name','')[:60]} | COLOR={color}")

# 2) Buscar catalogs adicionales para colores sin catalog oficial (Rojo, Aqua)
for q in ["JBL Go 4 Rojo","JBL Go 4 Aqua","JBL Go 4 Rosa"]:
    s=requests.get(f"https://api.mercadolibre.com/products/search?site_id=MLM&q={q}&limit=3",headers=HJ).json()
    print(f"\nsearch '{q}':")
    for p in (s.get("results") or [])[:5]:
        attrs={a.get("id"):a.get("value_name") for a in (p.get("attributes") or [])}
        if "Go 4" in p.get("name",""):
            print(f"  {p.get('id')} | {p.get('name')[:55]} | COLOR={attrs.get('COLOR')}")
            c=attrs.get("COLOR")
            if c and c not in color_to_cpid:
                color_to_cpid[c]=p.get("id")

# 3) Obtener pics por color de la Go 4 unificada de Juan (reutilizar)
juan_unified=requests.get("https://api.mercadolibre.com/items/MLM2883448187",headers=HJ).json()
color_pics={}
for v in (juan_unified.get("variations") or []):
    color=None
    for ac in (v.get("attribute_combinations") or []):
        if ac.get("id")=="COLOR": color=ac.get("value_name"); break
    pids=v.get("picture_ids") or []
    if not pids:
        pids=[p.get("id") for p in (v.get("pictures") or [])]
    color_pics[color]=pids
    print(f"  pics {color}: {len(pids)}")

# 4) Para cada cuenta, re-subir pics a su account y crear catalog-listing por color
def reupload_pics(AT, pids):
    out=[]
    for pid in pids:
        try:
            img=requests.get(f"https://http2.mlstatic.com/D_{pid}-O.jpg",timeout=15).content
            if len(img)<2000: continue
            rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
                headers={"Authorization":f"Bearer {AT}"},
                files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
            if rp.status_code in (200,201): out.append(rp.json()["id"])
        except: pass
    return out

ACCOUNTS=[
    ("JUAN",os.environ["MELI_REFRESH_TOKEN"],"new"),
    ("RAYMUNDO",os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"],"used"),
]

RESULTS={}
for label,rt,cond in ACCOUNTS:
    AT=get_token(rt)
    H={"Authorization":f"Bearer {AT}","Content-Type":"application/json"}
    print(f"\n=== {label} ({cond}) ===")
    RESULTS[label]=[]
    for color,cpid in color_to_cpid.items():
        pics=color_pics.get(color,[])[:3]
        if not pics:
            print(f"  {color}: sin pics, skip")
            continue
        new_pics=reupload_pics(AT,pics)
        if not new_pics:
            print(f"  {color}: upload fallo, skip")
            continue
        body={
            "site_id":"MLM",
            "catalog_product_id":cpid,
            "catalog_listing":True,
            "price":599,
            "available_quantity":10,
            "condition":cond,
            "listing_type_id":"gold_pro",
            "currency_id":"MXN",
            "buying_mode":"buy_it_now",
            "sale_terms":[
                {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                {"id":"WARRANTY_TIME","value_name":"30 días"},
            ],
            "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
            "pictures":[{"id":p} for p in new_pics],
        }
        rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
        if rp.status_code in (200,201):
            iid=rp.json()["id"]
            print(f"  {color} {cpid}: OK {iid}")
            RESULTS[label].append({"color":color,"id":iid,"cpid":cpid})
        else:
            print(f"  {color} {cpid}: {rp.status_code} {rp.text[:250]}")
        time.sleep(2)

print("\n=== RESUMEN ===")
for acc,items in RESULTS.items():
    print(f"\n{acc}: {len(items)} publicaciones catalog creadas")
    for it in items:
        print(f"  {it['color']}: {it['id']} (cpid={it['cpid']})")
