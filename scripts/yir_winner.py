import os,json,requests,time
RT_Y=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
def tok(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt}).json()["access_token"]
TY=tok(RT_Y); TW=tok(RT_W)
HY={"Authorization":f"Bearer {TY}","Content-Type":"application/json"}
HW={"Authorization":f"Bearer {TW}","Content-Type":"application/json"}

def pic_url(p):
    return p.get("source") or p.get("secure_url") or p.get("url") or ""

WIL={"go4_rojo":"MLM2910806817","go3_negro":"MLM2910806845","sony":"MLM2911238257"}
wp={}
for k,iid in WIL.items():
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=HW).json()
    wp[k]={"id":iid,"price":g.get("price"),"title":g.get("title"),"cpid":g.get("catalog_product_id"),"st":g.get("status"),
           "pics":[pic_url(p) for p in (g.get("pictures") or [])][:8],
           "category_id":g.get("category_id"),"listing_type_id":g.get("listing_type_id") or "gold_pro",
           "sale_terms":g.get("sale_terms") or [],"shipping":g.get("shipping") or {}}
print("WIL:",json.dumps({k:{"p":v["price"],"cpid":v["cpid"],"t":(v["title"] or "")[:60]} for k,v in wp.items()},ensure_ascii=False))

YIR={"go4_rojo":"MLM5291785036","go3_negro":"MLM5291788562"}
results=[]
for k,iid in YIR.items():
    target_price=max(int(wp[k]["price"])-1,400)
    a=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HY,json={"status":"active","price":target_price,"available_quantity":1})
    print(f"ACT {iid} -> ${target_price} http={a.status_code} {a.text[:200]}")
    results.append({"act":iid,"target":target_price,"http":a.status_code})
    time.sleep(0.3)

sony=wp["sony"]
sony_target=max(int(sony["price"])-1,400)
cbody={"catalog_listing":True,"catalog_product_id":sony["cpid"],"price":sony_target,"currency_id":"MXN","available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":sony["listing_type_id"],"condition":"new"}
cr=requests.post("https://api.mercadolibre.com/items",headers=HY,json=cbody)
print("CLONE_SONY http=",cr.status_code,cr.text[:500])
sony_new_id=cr.json().get("id") if cr.status_code<300 else None
results.append({"clone":"sony","http":cr.status_code,"new_id":sony_new_id,"err":(cr.text[:300] if cr.status_code>=400 else None)})

print("FINAL:",json.dumps({"wilbert":{k:v["price"] for k,v in wp.items()},"results":results},indent=2))
