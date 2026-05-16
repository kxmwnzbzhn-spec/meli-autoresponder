import os,json,requests,time
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
def tok(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json()["access_token"]
TW=tok(RT_W); TY=tok(RT_Y)
HW={"Authorization":f"Bearer {TW}"}
HWJ={"Authorization":f"Bearer {TW}","Content-Type":"application/json"}
HY={"Authorization":f"Bearer {TY}","Content-Type":"application/json"}

def upload_pic(t,u):
    img=requests.get(u,timeout=20)
    if img.status_code!=200: return None
    files={"file":("p.jpg",img.content,"image/jpeg")}
    r=requests.post("https://api.mercadolibre.com/pictures/items/upload",headers={"Authorization":f"Bearer {t}"},files=files)
    return r.json().get("id") if r.status_code<300 else None

WB=["MLM2916921591","MLM2916932945","MLM2916672499","MLM2916921745","MLM2916672931","MLM2916897215"]
pairs=[]
for wb_id in WB:
    g=requests.get(f"https://api.mercadolibre.com/items/{wb_id}",headers=HW).json()
    if not g.get("id"):
        print(f"{wb_id} SKIP - no data")
        continue
    title=g.get("title","")
    cat=g.get("category_id")
    cpid=g.get("catalog_product_id")
    p_w=int(g.get("price",0) or 0)
    target=max(p_w-1,200)
    pic_urls=[(p.get("url") or p.get("secure_url")) for p in (g.get("pictures") or [])][:8]
    desc=requests.get(f"https://api.mercadolibre.com/items/{wb_id}/description",headers=HW).json().get("plain_text") or ""
    print(f"\n{wb_id} '{title[:50]}' cat={cat} cpid={cpid} p_w=${p_w} → ${target}")
    pic_ids=[]
    for u in pic_urls:
        pid=upload_pic(TY,u)
        if pid: pic_ids.append(pid)
    print(f"  uploaded {len(pic_ids)} pics")
    body={
        "title":title,"category_id":cat,"price":target,"currency_id":"MXN",
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
        nid=r.json().get("id")
        print(f"  NEW_ID={nid}")
        if desc:
            d=requests.post(f"https://api.mercadolibre.com/items/{nid}/description",headers=HY,json={"plain_text":desc})
            if d.status_code>=300:
                d=requests.put(f"https://api.mercadolibre.com/items/{nid}/description",headers=HY,json={"plain_text":desc})
        pairs.append((wb_id,nid,title[:40],p_w))
        # Pause Wilbert source
        rp=requests.put(f"https://api.mercadolibre.com/items/{wb_id}",headers=HWJ,json={"status":"paused"})
        print(f"  PAUSE Wilbert http={rp.status_code}")
    else:
        print(f"  ERR: {r.text[:400]}")
    time.sleep(1)

print("\nPAIRS_JSON:"+json.dumps(pairs))
