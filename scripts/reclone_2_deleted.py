import os,requests,json
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
def tok(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()["access_token"]
TW=tok(RT_W); TY=tok(RT_Y)
HW={"Authorization":f"Bearer {TW}"}
HY={"Authorization":f"Bearer {TY}","Content-Type":"application/json"}

def upload_pic(token,url):
    img=requests.get(url,timeout=20)
    if img.status_code!=200: return None
    files={"file":("p.jpg",img.content,"image/jpeg")}
    r=requests.post("https://api.mercadolibre.com/pictures/items/upload",headers={"Authorization":f"Bearer {token}"},files=files)
    return r.json().get("id") if r.status_code<300 else None

PAIRS={"MLM2916649417":"Jo Milano Spades","MLM2916897121":"Orientica Amber Rouge"}
results=[]
for wb_id, name in PAIRS.items():
    g=requests.get(f"https://api.mercadolibre.com/items/{wb_id}",headers=HW).json()
    price_w=int(g.get("price",0))
    target=max(price_w-1,200)
    cat_id=g.get("category_id")
    cpid=g.get("catalog_product_id")
    title=g.get("title")
    desc=requests.get(f"https://api.mercadolibre.com/items/{wb_id}/description",headers=HW).json().get("plain_text") or ""
    pic_urls=[(p.get("url") or p.get("secure_url")) for p in (g.get("pictures") or [])][:8]
    pic_ids=[]
    for u in pic_urls:
        pid=upload_pic(TY,u)
        if pid: pic_ids.append(pid)
    print(f"\n{wb_id} ({name}): price_w=${price_w} target=${target} pics={len(pic_ids)}")
    body={
        "title":title,"category_id":cat_id,"price":target,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now",
        "listing_type_id":g.get("listing_type_id") or "gold_pro",
        "condition":g.get("condition","new"),
        "pictures":[{"id":p} for p in pic_ids],
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"drop_off"},
    }
    if cpid:
        body["catalog_listing"]=True
        body["catalog_product_id"]=cpid
    r=requests.post("https://api.mercadolibre.com/items",headers=HY,json=body)
    print(f"  POST http={r.status_code}")
    if r.status_code<300:
        new=r.json(); nid=new.get("id")
        print(f"  NEW_ID={nid} price=${new.get('price')}")
        if desc:
            d=requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=HY,json={"plain_text":desc})
            if d.status_code>=300:
                d=requests.put(f"https://api.mercadolibre.com/items/{nid}/description",headers=HY,json={"plain_text":desc})
            print(f"  DESC http={d.status_code}")
        results.append((wb_id,nid))
    else:
        print(f"  ERR: {r.text[:400]}")
print("\nPAIRS_UPDATE:")
for w,n in results: print(f"  {w} → {n}")
