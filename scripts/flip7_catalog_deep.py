import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}

# Buscar todos catalog products JBL Flip 7
print("=== SEARCH BROAD JBL Flip 7 catalogs ===")
for q in ["JBL Flip 7","Bocina JBL Flip 7","JBL Flip7","JBLFLIP7"]:
    s=requests.get(f"https://api.mercadolibre.com/products/search?site_id=MLM&q={q}&limit=20",headers=H).json()
    for p in (s.get("results") or [])[:20]:
        name=p.get("name","")
        if "Flip 7" in name or "FLIP7" in name.upper() or "Flip7" in name:
            color=None
            for a in (p.get("attributes") or []):
                if a.get("id")=="COLOR": color=a.get("value_name"); break
            pics=len(p.get("pictures") or [])
            kids=len(p.get("children_ids") or [])
            print(f"  {p.get('id')} | {name[:70]} | COLOR={color} | pics={pics} kids={kids}")

# Explorar CHILDREN de cada catalog encontrado para buscar Rojo y Morado
print("\n=== DEEP children de Flip 7 parents ===")
parents=["MLM64166697","MLM63648344","MLM62944208","MLM47584787","MLM65258828"]
for cpid in parents:
    try:
        p=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=10).json()
        for kid in (p.get("children_ids") or []):
            pk=requests.get(f"https://api.mercadolibre.com/products/{kid}",headers=H,timeout=10).json()
            color=None
            for a in (pk.get("attributes") or []):
                if a.get("id")=="COLOR": color=a.get("value_name"); break
            pics=len(pk.get("pictures") or [])
            print(f"  [{cpid}] child {kid} | {pk.get('name','')[:60]} | COLOR={color} | pics={pics}")
    except: pass

# Items live search por color especifico con mas variaciones de query
print("\n=== SEARCH ITEMS LIVE Flip 7 por color ===")
for color in ["Rojo","Rojo red","Morado","purple","violeta","lila"]:
    s=requests.get(f"https://api.mercadolibre.com/sites/MLM/search?q=JBL+Flip+7+{color}&category=MLM59800&limit=20&condition=new",headers=H).json()
    print(f"\n  Query '{color}': {s.get('paging',{}).get('total',0)} results")
    for r_ in (s.get("results") or [])[:5]:
        t=r_.get("title","")
        if "Flip 7" in t or "Flip7" in t:
            print(f"    {r_.get('id')} | {t[:70]}")
