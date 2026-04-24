import os,requests,json,time

ITEMS=["MLM5226013726","MLM5226013748","MLM5226014378","MLM5226014380","MLM5226014888","MLM5226039220","MLM5226052484","MLM5226091240"]

# Claribel token
rc=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]}).json()
TOK_C=rc["access_token"]
HC={"Authorization":f"Bearer {TOK_C}","Content-Type":"application/json"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=HC).json()
print(f"Claribel: {me.get('nickname')} ({me.get('id')})")

# Intentar obtener info de items (probar con token Claribel primero, luego otros tokens si no)
ACCOUNTS={
    "CLARIBEL":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"],
    "JUAN":os.environ["MELI_REFRESH_TOKEN"],
    "ASVA":os.environ["MELI_REFRESH_TOKEN_ASVA"],
    "RAYMUNDO":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"],
}

# Cache de tokens
TOKENS={}
for label,rt in ACCOUNTS.items():
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()
    if "access_token" in r: TOKENS[label]=r["access_token"]

# Buscar cada item en qué cuenta está
items_data={}
for iid in ITEMS:
    found=False
    for label,t in TOKENS.items():
        H={"Authorization":f"Bearer {t}"}
        d=requests.get(f"https://api.mercadolibre.com/items/{iid}?include_attributes=all",headers=H,timeout=15).json()
        if d.get("id")==iid and "error" not in d:
            seller_id=d.get("seller_id")
            items_data[iid]={"source":label,"data":d,"desc":""}
            try:
                desc=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,timeout=10).json()
                items_data[iid]["desc"]=desc.get("plain_text","")
            except: pass
            print(f"  {iid} [{label}] status={d.get('status')} cat={d.get('category_id')} '{d.get('title','')[:50]}' price=${d.get('price')}")
            found=True
            break
    if not found:
        print(f"  {iid}: NO encontrado en ninguna cuenta")

# Republicar en Claribel cada item activo/cerrado con el mismo setup
print("\n=== REPUBLICAR EN CLARIBEL ===")
results=[]
for iid,info in items_data.items():
    d=info["data"]
    desc=info["desc"]
    # re-subir pics
    def reup(pid):
        try:
            img=requests.get(f"https://http2.mlstatic.com/D_{pid}-O.jpg",timeout=15).content
            if len(img)<2000: return None
            rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
                headers={"Authorization":f"Bearer {TOK_C}"},
                files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
            return rp.json().get("id") if rp.status_code in (200,201) else None
        except: return None
    
    pics=[p.get("id") for p in (d.get("pictures") or [])][:10]
    new_pics=[]
    for p in pics:
        n=reup(p)
        if n: new_pics.append(n)
    
    # Limpiar atributos (quitar auto generados)
    BAD_ATTR={"EAN","UPC","MPN","SELLER_SKU","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","GRADING","LINE","DETAILED_MODEL"}
    attrs=[]
    for a in (d.get("attributes") or []):
        aid=a.get("id")
        if aid in BAD_ATTR: continue
        val=a.get("value_name") or a.get("values",[{}])[0].get("name") if a.get("values") else None
        if val:
            attrs.append({"id":aid,"value_name":val})
    
    # Construir body
    body={
        "site_id":"MLM",
        "title":d.get("title"),
        "category_id":d.get("category_id"),
        "currency_id":d.get("currency_id","MXN"),
        "price":d.get("price"),
        "available_quantity":d.get("available_quantity",10),
        "listing_type_id":d.get("listing_type_id","gold_special"),
        "condition":d.get("condition"),
        "buying_mode":d.get("buying_mode","buy_it_now"),
        "sale_terms":d.get("sale_terms",[]),
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
        "pictures":[{"id":p} for p in new_pics],
        "attributes":attrs,
    }
    # Si tiene variaciones
    if d.get("variations"):
        variations=[]
        for v in d.get("variations"):
            pids=v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])]
            # re-upload variation pics (skip if already in new_pics)
            new_var_pics=[]
            for p in pids[:5]:
                n=reup(p)
                if n: new_var_pics.append(n)
            if not new_var_pics: new_var_pics=new_pics[:3]
            variations.append({
                "price":v.get("price") or d.get("price"),
                "available_quantity":v.get("available_quantity") or 1,
                "attribute_combinations":v.get("attribute_combinations",[]),
                "picture_ids":new_var_pics,
            })
        body["variations"]=variations
    
    rp=requests.post("https://api.mercadolibre.com/items",headers=HC,json=body,timeout=60)
    print(f"\n{iid} -> ", end="")
    if rp.status_code in (200,201):
        new_id=rp.json()["id"]
        print(f"OK {new_id}")
        # copiar descripcion
        if desc:
            rd=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",headers=HC,json={"plain_text":desc},timeout=20)
            print(f"  desc: {rd.status_code}")
        results.append({"old":iid,"new":new_id,"title":d.get("title","")[:50]})
    else:
        err=rp.json()
        print(f"{rp.status_code} {str(err)[:400]}")
    time.sleep(2)

print("\n=== RESUMEN ===")
for r in results:
    print(f"  {r['old']} -> {r['new']}: {r['title']}")
