import os,json,requests,time
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
RT_D=os.environ["MELI_REFRESH_TOKEN_DILCIE"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]

def tok(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json().get("access_token")

TW=tok(RT_W); TD=tok(RT_D)
print(f"TW={'OK' if TW else 'FAIL'} TD={'OK' if TD else 'FAIL'}")
if not TD:
    print("ERR Dilcie auth"); raise SystemExit(1)
HW={"Authorization":f"Bearer {TW}"}
HD={"Authorization":f"Bearer {TD}","Content-Type":"application/json"}

# Verify Dilcie active
me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {TD}"}).json()
print(f"Dilcie: uid={me.get('id')} nick={me.get('nickname')}")
if not me.get("id"):
    print(f"ERR: {me}"); raise SystemExit(1)

ITEMS=["MLM2910806845","MLM2914422351","MLM2910768325","MLM2910806881","MLM2910457917",
       "MLM2910768333","MLM2910768335","MLM2910806871","MLM2910768369","MLM5351937060",
       "MLM5354755946","MLM5297098664","MLM2931341689","MLM5297087174","MLM2931612609",
       "MLM2931612611","MLM2937969761","MLM5337919270","MLM5337919290"]

def safe_get(url,headers,tries=3):
    for i in range(tries):
        try:
            r=requests.get(url,headers=headers,timeout=20)
            if r.status_code==200:
                d=r.json()
                if isinstance(d,dict): return d
                print(f"    WARN: response type={type(d).__name__} val={str(d)[:200]}")
            else:
                print(f"    WARN: http={r.status_code} body={r.text[:200]}")
        except Exception as e:
            print(f"    WARN: try {i+1} exception {e}")
        time.sleep(1+i)
    return None

results=[]
for idx,wb_id in enumerate(ITEMS,1):
    print(f"\n[{idx}/19] {wb_id}")
    g=safe_get(f"https://api.mercadolibre.com/items/{wb_id}",HW)
    if not g:
        print(f"  ✗ no data")
        results.append({"src":wb_id,"err":"no data"})
        continue
    title=g.get("title","")
    cat=g.get("category_id")
    cpid=g.get("catalog_product_id")
    price=int(g.get("price") or 0)
    cond=g.get("condition","new")
    ltype=g.get("listing_type_id") or "gold_pro"
    print(f"  '{title[:55]}' ${price} cpid={cpid}")
    
    body={
        "title":title,"category_id":cat,"price":price,"currency_id":"MXN",
        "available_quantity":1,
        "buying_mode":"buy_it_now","listing_type_id":ltype,"condition":cond,
        "sale_terms":[
            {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
            {"id":"WARRANTY_TIME","value_name":"90 días"}
        ],
    }
    if cpid:
        body["catalog_listing"]=True
        body["catalog_product_id"]=cpid
    
    try:
        r=requests.post("https://api.mercadolibre.com/items",headers=HD,json=body,timeout=30)
        if r.status_code<300:
            new=r.json()
            nid=new.get("id")
            print(f"  ✓ NEW_ID={nid} ${new.get('price')}")
            results.append({"src":wb_id,"new":nid,"price":price,"title":title[:40]})
        else:
            err_txt=r.text[:300]
            print(f"  ✗ http={r.status_code} {err_txt}")
            results.append({"src":wb_id,"http":r.status_code,"err":err_txt})
    except Exception as e:
        print(f"  ✗ exception {e}")
        results.append({"src":wb_id,"err":str(e)[:150]})
    
    time.sleep(0.8)
    if idx%5==0 and idx<len(ITEMS):
        print(f"\n--- batch sleep 3s ---")
        time.sleep(3)

print("\n=== SUMMARY ===")
ok=[r for r in results if r.get("new")]
print(f"OK: {len(ok)}/{len(results)}")
print("\n--- CLONADAS ---")
for r in results:
    if r.get("new"): print(f"  {r['src']} → {r['new']}  ${r['price']}  '{r['title']}'")
print("\n--- FALLIDAS ---")
for r in results:
    if not r.get("new"): print(f"  {r['src']}: {r.get('err','?')[:120]}")
