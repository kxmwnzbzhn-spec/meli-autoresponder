import os,requests,time,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}

# Cargar stock config
try:
    with open("stock_config.json") as f: sc=json.load(f)
except: sc={}

# 1) Reactivar auto_replenish de Flip 7 Negra (MLM2880754185) y Morada (MLM2880758743) con stock real
FLIP_RESUME=[
    ("MLM2880754185","Flip 7","Negra",179),
    ("MLM2880758743","Flip 7","Morada",59),
]
for iid,m,c,stock in FLIP_RESUME:
    sc[iid]={"real_stock":stock,"sku":f"FLIP7-{c.upper()}","label":f"{m} {c}","auto_replenish":True,"replenish_quantity":1,"min_visible_stock":1,"deleted":False}
    print(f"RESUME {iid} [{m} {c}] stock={stock}")

# 2) Crear catalog listings para items que no tengamos activos en catalogo
# (model, color, price, stock, cpid)
TO_CREATE=[
    ("Flip 7","Azul",499,63,"MLM57073449"),
    ("Flip 7","Rojo",499,35,"MLM48958711"),
    ("Charge 6","Azul",699,4,"MLM62088361"),
    ("Charge 6","Rojo",699,22,"MLM58806550"),
    ("Charge 6","Camuflaje",699,2,"MLM58829227"),
    ("Charge 6","Negro",699,2,"MLM51435334"),
    ("Clip 5","Morado",399,11,"MLM45586155"),
    ("Grip","Negro",399,5,"MLM59802579"),
    ("Go 4","Rojo",399,19,"MLM64389753"),
    ("Go 4","Rosa",399,10,"MLM65831856"),
    ("Go 4","Azul",399,9,None),
    ("Go 3","Negro",399,5,"MLM44709174"),
]

def get_prod(cpid):
    if not cpid: return None
    r=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15)
    return r.json() if r.status_code==200 else None

def publish_catalog(cpid,price):
    body={
        "catalog_product_id":cpid,
        "catalog_listing":True,
        "price":price,
        "currency_id":"MXN",
        "available_quantity":1,
        "condition":"new",
        "listing_type_id":"gold_pro",
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"}
        ]
    }
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=30)
    # Try with title/category fallback
    if r.status_code not in (200,201):
        prod=get_prod(cpid)
        if prod:
            cat=prod.get("category_details",{}).get("id") or "MLM59800"
            body2={**body,"title":prod.get("name","")[:60],"category_id":cat}
            r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body2,timeout=30)
    if r.status_code in (200,201):
        return r.json().get("id"), None
    return None, str(r.json())[:400]

ok=0; err=0
for model,color,price,stock,cpid in TO_CREATE:
    if not cpid:
        # buscar
        q=f"JBL {model} {color}"
        rs=requests.get(f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={q.replace(' ','+')}",headers=H,timeout=15).json()
        for it in rs.get("results",[])[:8]:
            nm=(it.get("name") or "").lower()
            if any(b in nm for b in ["funda","case","cover","tester"]): continue
            if model.lower() in nm and color.lower() in nm:
                cpid=it.get("id"); break
    if not cpid:
        print(f"  NO CPID {model} {color}")
        err+=1; continue
    nid,e=publish_catalog(cpid,price)
    if nid:
        print(f"  OK {model} {color} -> {nid} (cpid={cpid}, stock real {stock})")
        sc[nid]={"real_stock":stock,"sku":f"CAT-{model.replace(' ','')}-{color.upper()}","label":f"Catalog {model} {color}","auto_replenish":True,"replenish_quantity":1,"min_visible_stock":1}
        ok+=1
    else:
        print(f"  ERR {model} {color} cpid={cpid}: {e[:200]}")
        err+=1
    time.sleep(2)

with open("stock_config.json","w") as f: json.dump(sc,f,indent=2,ensure_ascii=False)
print(f"\n=== {ok} catalog listings OK, {err} ERR ===")
