import os,json,base64,requests,urllib.parse
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# === FIX 1: Flip 7 espejo — visible 1/color ===
iid_f7="MLM5347216886"
g=requests.get(f"https://api.mercadolibre.com/items/{iid_f7}",headers=H).json()
vrs=g.get("variations",[])
if vrs:
    new_vrs=[{"id":v["id"],"available_quantity":1} for v in vrs]
    r=requests.put(f"https://api.mercadolibre.com/items/{iid_f7}",headers=H,json={"variations":new_vrs})
    print(f"FIX F7 {iid_f7} 1/color http={r.status_code}")
    g2=requests.get(f"https://api.mercadolibre.com/items/{iid_f7}?attributes=id,available_quantity,variations",headers=H).json()
    print(f"  AFTER total_qty={g2.get('available_quantity')}")

# === Search Go 4 Camuflaje alternativos ===
print("\n=== Buscando catálogos alternativos Go 4 Camuflaje ===")
for q in ["jbl go 4 camuflaje","jbl go 4 camo","go 4 camuflado"]:
    url=f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={urllib.parse.quote(q)}&limit=20"
    r=requests.get(url,headers=H).json()
    for p in r.get("results",[]):
        n=(p.get("name") or "").lower()
        attrs={a.get("id"):a.get("value_name") for a in (p.get("attributes") or [])}
        col=(attrs.get("COLOR") or "").lower()
        if "go 4" in n and ("camuflaj" in n+col or "camo" in n+col or "camuflad" in n+col):
            pid=p.get("id")
            pd=requests.get(f"https://api.mercadolibre.com/products/{pid}",headers=H).json()
            parent=pd.get("parent_id") or "?"
            print(f"  CPID={pid} parent={parent} COLOR={attrs.get('COLOR')} name={p.get('name','')[:55]}")

# === Try clone with each ===
print("\n=== Intentando publicar clones (varios CPIDs) ===")
TRY=["MLM37361021"]  # original que estaba blocked, lo probamos otra vez por si se desbloqueó
# Vamos a hacer una búsqueda y agregar todos los Camuflaje que encontremos diferentes
for q in ["jbl go 4 camuflaje","go 4 camuflado","go 4 camo"]:
    url=f"https://api.mercadolibre.com/products/search?status=active&site_id=MLM&q={urllib.parse.quote(q)}&limit=20"
    r=requests.get(url,headers=H).json()
    for p in r.get("results",[]):
        n=(p.get("name") or "").lower()
        attrs={a.get("id"):a.get("value_name") for a in (p.get("attributes") or [])}
        col=(attrs.get("COLOR") or "").lower()
        if "go 4" in n and ("camuflaj" in n+col or "camo" in n+col or "camuflad" in n+col):
            if p.get("id") not in TRY: TRY.append(p.get("id"))

results=[]
for cpid in TRY[:6]:
    pd=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H).json()
    body={
        "title": pd.get("name",""),
        "category_id": "MLM59800",
        "catalog_listing": True,
        "catalog_product_id": cpid,
        "price": 599,
        "currency_id": "MXN",
        "available_quantity": 1,
        "buying_mode": "buy_it_now",
        "listing_type_id": "gold_pro",
        "condition": "new",
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"90 días"}
        ]
    }
    r=requests.post("https://api.mercadolibre.com/items",headers=H,json=body)
    if r.status_code<300:
        new=r.json()
        print(f"  ✓ CPID={cpid} → NEW_ID={new.get('id')} price=$599")
        results.append({"cpid":cpid,"new_id":new.get("id"),"name":pd.get("name","")[:60]})
        break  # one is enough
    else:
        e=r.json() if r.text.startswith("{") else {"err":r.text[:200]}
        cause=e.get("cause",[{}])[0].get("code","?") if isinstance(e.get("cause"),list) else "?"
        print(f"  ✗ CPID={cpid} http={r.status_code} cause={cause}")
        results.append({"cpid":cpid,"http":r.status_code,"cause":cause})

print("\n=== SUMMARY ===")
print(json.dumps(results,indent=2,ensure_ascii=False))
