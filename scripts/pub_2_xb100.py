import os, requests, time
API="https://api.mercadolibre.com"
tok=requests.post(f"{API}/oauth/token",data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]
},timeout=20).json()
T=tok["access_token"]
print(f"NEW_RT_CLARIBEL={tok.get('refresh_token')}")
H={"Authorization":f"Bearer {T}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=10).json()
UID=me["id"]

# Existing CPIDs in Claribel
own=dict()  # cpid -> (item_id, status, price)
for st in ("active","paused","under_review"):
    off=0
    while True:
        r=requests.get(f"{API}/users/{UID}/items/search?status={st}&limit=50&offset={off}",headers=H,timeout=15).json()
        res=r.get("results") or []
        for i in range(0,len(res),20):
            batch=",".join(res[i:i+20])
            mg=requests.get(f"{API}/items",headers=H,params={"ids":batch,"attributes":"id,catalog_product_id,status,price"},timeout=20).json()
            for x in mg:
                if x.get("code")==200:
                    b=x["body"]
                    cp=b.get("catalog_product_id")
                    if cp: own[cp]=(b["id"],b.get("status"),b.get("price"))
        if len(res)<50 or off>1500: break
        off+=50
print(f"Claribel CPIDs: {len(own)}")

TARGETS=[
  {"cpid":"MLM25912333","price":799,"title":"Sony SRS-XB100 Altavoz De Viaje Inalámbrico Bluetooth Negro"},
  {"cpid":"MLM2023522170","price":699,"title":"Sony SRS-XB100 Altavoz Bluetooth Negro Nuevo Caja Abierta"},
]

results=[]
for t in TARGETS:
    cpid=t["cpid"]; price=t["price"]; title=t["title"]
    print(f"\n=== {cpid} ===")
    if cpid in own:
        iid,st,cur=own[cpid]
        print(f"  ⚠ Claribel ALREADY has cpid {cpid} as {iid} status={st} ${cur}")
        # Set price
        body={"price":price}
        if st=="paused": body["status"]="active"; body["available_quantity"]=1
        r=requests.put(f"{API}/items/{iid}",headers=HJ,json=body,timeout=20)
        print(f"  PUT price=${price}: {r.status_code} {r.text[:150] if r.status_code>=400 else 'OK'}")
        results.append(("REUSED",cpid,iid,price,title))
        continue

    # Get category from /products/{cpid}/items first offer
    cat="MLM59800"  # bocinas default
    try:
        off_r=requests.get(f"{API}/products/{cpid}/items?limit=3",headers=H,timeout=10).json()
        for o in (off_r.get("results") or [])[:3]:
            iid_o=o.get("item_id")
            if iid_o:
                tmp=requests.get(f"{API}/items/{iid_o}",headers=H,params={"attributes":"category_id"},timeout=10).json()
                if tmp.get("category_id"):
                    cat=tmp["category_id"]; break
    except: pass
    print(f"  category={cat}")

    base={"site_id":"MLM","category_id":cat,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":"gold_pro","condition":"new",
        "catalog_product_id":cpid,"catalog_listing":True,
        "shipping":{"mode":"me2","free_shipping":True}}
    r=requests.post(f"{API}/items",headers=HJ,json=base,timeout=40)
    if r.status_code not in (200,201):
        r=requests.post(f"{API}/items",headers=HJ,json={**base,"title":title[:60]},timeout=40)
    if r.status_code in (200,201):
        d=r.json()
        print(f"  ✓ PUBLISHED: {d['id']} {d.get('status')} ${d.get('price')}")
        print(f"    url={d.get('permalink')}")
        results.append(("NEW",cpid,d["id"],price,title))
    else:
        print(f"  ✗ FAIL {r.status_code}: {r.text[:400]}")
        results.append(("FAIL",cpid,None,price,title))
    time.sleep(1)

print(f"\n=== RESUMEN ===")
for kind,cp,iid,pr,title in results:
    print(f"  {kind} {cp} → {iid} ${pr} | {title[:60]}")
