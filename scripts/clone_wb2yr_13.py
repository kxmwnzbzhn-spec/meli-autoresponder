import os,json,requests,time
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
def tok(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()["access_token"]
TW=tok(RT_W); TY=tok(RT_Y)
HW={"Authorization":f"Bearer {TW}","Content-Type":"application/json"}
HY={"Authorization":f"Bearer {TY}","Content-Type":"application/json"}

ITEMS=["MLM5265893750","MLM5309659262","MLM2908793361","MLM2916649417","MLM2916897121","MLM2908818917","MLM2908867469","MLM2908818183","MLM2916908777","MLM2916672247","MLM2916676513","MLM2916908753","MLM2916921559","MLM2916700919"]

def upload_pic(token,url):
    img=requests.get(url,timeout=20)
    if img.status_code!=200: return None
    files={"file":("p.jpg",img.content,"image/jpeg")}
    r=requests.post("https://api.mercadolibre.com/pictures/items/upload",
                    headers={"Authorization":f"Bearer {token}"}, files=files)
    return r.json().get("id") if r.status_code<300 else None

results=[]
for iid in ITEMS:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=HW).json()
    if g.get("status")=="closed" or not g.get("id"):
        print(f"\n{iid}: SKIP (status={g.get('status')})")
        results.append({"iid":iid,"skip":"closed"})
        continue
    title=g.get("title","")
    cat_id=g.get("category_id")
    cpid=g.get("catalog_product_id")
    price_w=int(g.get("price",0) or 0)
    price_y=max(price_w-1,100)
    pic_urls=[(p.get("url") or p.get("secure_url")) for p in (g.get("pictures") or [])][:8]
    desc=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=HW).json().get("plain_text") or ""
    print(f"\n{iid}: '{title[:55]}' cat={cat_id} cpid={cpid} price_w=${price_w} → price_y=${price_y}")
    
    # Upload pics into Yiriam account
    pic_ids=[]
    for u in pic_urls:
        pid=upload_pic(TY,u)
        if pid: pic_ids.append(pid)
    print(f"  uploaded {len(pic_ids)} pics to Yiriam")
    
    body={
        "title": title,
        "category_id": cat_id,
        "price": price_y,
        "currency_id":"MXN",
        "available_quantity":1,
        "buying_mode":"buy_it_now",
        "listing_type_id": g.get("listing_type_id") or "gold_pro",
        "condition": g.get("condition","new"),
        "pictures": [{"id":p} for p in pic_ids],
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"30 días"}
        ],
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"drop_off"},
    }
    if cpid:
        body["catalog_listing"]=True
        body["catalog_product_id"]=cpid
    # try post
    r=requests.post("https://api.mercadolibre.com/items",headers=HY,json=body)
    if r.status_code>=300:
        # retry without shipping
        body2=dict(body); body2.pop("shipping",None)
        r=requests.post("https://api.mercadolibre.com/items",headers=HY,json=body2)
    print(f"  POST http={r.status_code}")
    if r.status_code<300:
        new=r.json(); nid=new.get("id")
        print(f"  NEW_ID={nid} price=${new.get('price')} status={new.get('status')}")
        # add description
        if desc:
            d=requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=HY,json={"plain_text":desc})
            if d.status_code>=300:
                d=requests.put(f"https://api.mercadolibre.com/items/{nid}/description",headers=HY,json={"plain_text":desc})
            print(f"  DESC http={d.status_code}")
        results.append({"wilbert":iid,"yiriam":nid,"price_w":price_w,"price_y":price_y,"title":title[:50]})
    else:
        print(f"  ERR: {r.text[:400]}")
        results.append({"wilbert":iid,"err":r.text[:300],"http":r.status_code})
    time.sleep(1)

print("\n=== SUMMARY ===")
print(json.dumps(results,indent=2,ensure_ascii=False))
